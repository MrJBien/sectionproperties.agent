# to run this script properly, enter "streamlit run main_streamlit.py" in the command line

import time, json
from xmlrpc import client
import numpy as np
import streamlit as st
from matplotlib.figure import Figure

from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig

from sectionproperties.pre import Material
from sectionproperties.pre.library import circular_hollow_section, elliptical_hollow_section, rectangular_hollow_section, polygon_hollow_section, i_section, mono_i_section, tapered_flange_i_section, channel_section, tapered_flange_channel, tee_section, angle_section, cee_section, zed_section, box_girder_section, bulb_section
from sectionproperties.analysis import Section


with open("tool_declaration.json", 'r') as f:
    tools = json.load(f)

# If you want to skip non-serializable objects (not just ndarrays)
class SelectiveEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            # Try to serialize the object normally
            return json.JSONEncoder.default(self, obj)
        except TypeError:
            # If it's not serializable, skip it
            return None 
      
# If you want to skip non-serializable objects (not just ndarrays)
class ConversionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        try:
            # Try to serialize the object normally
            return json.JSONEncoder.default(self, obj)
        except TypeError:
            # If it's not serializable and not an ndarray, skip it
            return None

def call_function(function_name: str, object_name: str = None, **kwargs) -> str:
    """
    Creates a string representation of a function or method call with keyword arguments.

    Args:
        function_name: The name of the function or method as a string.
        object_name: (Optional) The name of the object if calling a method.
                     If provided, the call will be formatted as "object_name.function_name(...)".
        **kwargs: Arbitrary keyword arguments to be included in the function/method call.

    Returns:
        A string representing the function or method call,
        e.g., "my_function(arg1=10, name='test')" or "my_object.my_method(param=True)".
    """
    # Format the keyword arguments into a string
    kwargs_str = []
    for key, value in kwargs.items():
        if isinstance(value, str):
            # Enclose string values in single quotes
            kwargs_str.append(f"{key}='{value}'")
        else:
            # For non-string values, use their direct string representation
            kwargs_str.append(f"{key}={value}")

    # Join the formatted keyword arguments with commas
    params_string = ", ".join(kwargs_str)

    # Prepend the object name if it's provided
    if object_name:
        full_function_call = f"{object_name}.{function_name}({params_string})"
    else:
        full_function_call = f"{function_name}({params_string})"
    return full_function_call


def call_LLM(client, model_id, config, user_prompt, history, tool_calls_log, tool_history_placeholder=None, sec=None, geom=None, stresses=None):
    figures = []
    history.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))

    try:
        response = client.models.generate_content(
            model=model_id,
            config=config,
            contents=history
        )
    except Exception as e:
        history.append(types.Content(role="model", parts=[types.Part(text=f"An error occurred: {str(e)}")]))
        return history, sec, geom, stresses, figures

    # Collect all function calls in this turn
    while response:
        function_calls = []
        # Check if we have valid candidates
        if not response.candidates:
             break

        candidate = response.candidates[0]
        
        # Check if content and parts exist
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                history.append(types.Content(role="model", parts=[part]))
                # check if the response is a function call
                if part.function_call:
                    function_calls.append(part.function_call)
        else:
             # If content is empty or blocked, stop the loop to avoid infinite loops or errors
             break

        # Prepare all function response parts
        function_response_parts = []
        for function_call in function_calls:            
            # Call the tool with arguments
            print(f"{"\033[90m"}logger: Calling tool {function_call.name} with args: {function_call.args}{"\033[0m"}\n")
            tool_calls_log.append(f"🛠️ {function_call.name} with args: {function_call.args}")

            if tool_history_placeholder:
                with tool_history_placeholder.container():
                    history_html = "".join([f"<div style='font-size: small; color: #808080; margin-bottom: 2px;'>{call}</div>" for call in tool_calls_log])
                    st.markdown(history_html, unsafe_allow_html=True)

            # Default tool result in case no handler matches
            tool_result = {
                "status": "error",
                "message": f"Tool '{function_call.name}' is not implemented or not available."
            }

            # For functions in the current global scope:
            if function_call.name in globals():
                func_obj = globals()[function_call.name]    
                srcmodule = func_obj.__module__ #module where the function is defined
            else:    
                srcmodule = None

            if srcmodule == "sectionproperties.pre.library.steel_sections":
                try:
                    ele_size = 10
                    geom = globals()[function_call.name](**function_call.args)
                    geom.material = Material(name="S235", elastic_modulus=210000, poissons_ratio=0.3, density=7.85e-6, yield_strength=235, color="cyan")
                    geom.create_mesh(mesh_sizes=ele_size)
                    sec = Section(geometry=geom)
                    
                    fig = Figure(figsize=(4.8, 3.6))
                    ax = fig.subplots()
                    sec.plot_mesh(materials=True, pause=False, ax=ax)
                    figures.append(fig)

                    tool_result = {
                        "status": "success",
                        "message": f"Geometry of the section generated and meshed successfully. A default element size of {ele_size} mm and Material {geom.material.name} was used. A plot was generated showing the section mesh.",
                        "next_steps_suggestion": "Would you like to evaluate the section properties or perform a stress analysis?",
                    }
                except Exception as e:
                    tool_result = {
                        "status": "error",
                        "message": f"Error calling {function_call.name}: {str(e)}"
                    }
            elif function_call.name == "calculate_geometric_properties":
                try:
                    sec.calculate_geometric_properties(**function_call.args)
                    
                    tool_result = {
                        "status": "success",
                        "message": f"Geometric section properties have been calculated successfully.",
                        "section_properties": json.dumps(sec.section_props.__dict__, indent=4, cls=SelectiveEncoder),
                        "next_steps_suggestion": "Would you like to calculate warping properties or perform a stress analysis?"
                    }            
                except Exception as e:
                    tool_result = {
                        "status": "error",
                        "message": f"Error calling {function_call.name}: {str(e)}"
                    }
            elif function_call.name == "calculate_warping_properties":
                try:
                    sec.calculate_warping_properties(**function_call.args)
                    
                    tool_result = {
                        "status": "success",
                        "message": f"Warping properties of the section have been calculated successfully.",
                        "warping_properties": json.dumps(sec.section_props.__dict__, indent=4, cls=SelectiveEncoder),
                        "next_steps_suggestion": "Would you like to continue with a stress analysis?"
                    }
                except Exception as e:
                    tool_result = {
                        "status": "error",
                        "message": f"Error calling {function_call.name}: {str(e)}"
                    }
            elif function_call.name == "calculate_stress":
                try:
                    stresses = sec.calculate_stress(**function_call.args)
                    
                    tool_result = {
                        "status": "success",
                        "message": f"Section stresses have been calculated successfully.",
                        "max_axial_stress": stresses.material_groups[0].stress_result.sig_zz.max(),
                        "max_shear_stress": stresses.material_groups[0].stress_result.sig_zxy.max(),
                        "max_von_mises_stress": stresses.material_groups[0].stress_result.sig_vm.max(),
                        "min_axial_stress": stresses.material_groups[0].stress_result.sig_zz.min(),
                        "min_shear_stress": stresses.material_groups[0].stress_result.sig_zxy.min(),
                        "min_von_mises_stress": stresses.material_groups[0].stress_result.sig_vm.min(),
                        "next_steps_suggestion": "Would you like to view the stress results? I could plot the Axial, Shear or von Mises stresses for you.",
                    }
                except Exception as e:
                    tool_result = {
                        "status": "error",
                        "message": f"Error calling {function_call.name}: {str(e)}"
                    }
            elif function_call.name == "plot_stress":
                try:
                    if stresses:
                        # Create a new Figure object explicitly
                        fig = Figure(figsize=(4.8, 3.6))
                        ax = fig.subplots()
                        stresses.plot_stress(**function_call.args, normalize=False, pause=False, ax=ax)
                        figures.append(fig)
                        
                        tool_result = {
                            "status": "success",
                            "message": f"Plot of {function_call.args.get('plot_type')} stresses generated.",
                            "plot_description": "A plot of the stresses over the section.",
                            "caption_suggestion": "Here's the section stress plot.",
                        }
                    else:
                        tool_result = {
                            "status": "error",
                            "message": "Stresses have not been calculated yet. Please calculate stresses before plotting."
                        }
                except Exception as e:
                    tool_result = {
                        "status": "error",
                        "message": f"Error calling {function_call.name}: {str(e)}"
                    }

            # elif function_call.name == "GoogleSearch":
            #     try:
            #         search_response = client.models.generate_content(
            #             model=model_id,
            #             config=GenerateContentConfig(
            #                 system_instruction="Perform an online search on basic section dimensions for standard steel sections in the web and output them in a structured way.",
            #                 tools=[types.Tool(google_search=types.GoogleSearch())],
            #             ),
            #             contents=history
            #         )

            #         if search_response.candidates and search_response.candidates[0].content and search_response.candidates[0].content.parts:
            #             search_text = search_response.candidates[0].content.parts[0].text
            #             tool_result = {"result": search_text}
            #         else:
            #             tool_result = {"status": "error", "message": "Google Search returned no content."}
                        
            #     except Exception as e:
            #         tool_result = {
            #             "status": "error",
            #             "message": f"Error performing Google Search: {str(e)}"
            #         }

            function_response_part = types.Part.from_function_response(
                name=function_call.name,
                response=tool_result,
            )
            function_response_parts.append(function_response_part)

        response = None

        if function_response_parts:
            history.append(types.Content(role="user", parts=function_response_parts))
            try:
                response = client.models.generate_content(
                    model=model_id, config=config, contents=history
                )
            except Exception as e:
                history.append(types.Content(role="model", parts=[types.Part(text=f"An error occurred: {str(e)}")]))
                response = None

    return history, sec if 'sec' in locals() else None, geom if 'geom' in locals() else None, stresses if 'stresses' in locals() else None, figures if 'figures' in locals() else None

def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.02)

def main():
    # Setup page configuration
    st.set_page_config(page_title="Sectionproperties Assistant", page_icon="🤖")

    # Sidebar for API Key and Privacy Info
    with st.sidebar:
        st.header("This application is powered by: ")
        st.subheader("1) Google Generative AI")
        user_api_key = st.text_input("Google API Key", type="password", help="Get your free key at https://aistudio.google.com/")
        
        st.subheader("🔒 Data Privacy (DSGVO/GDPR)")
        st.info(
            "This application acts as a user interface. By using it:\n"
            "1. Your inputs are sent to Google's Generative AI servers for processing. More info regarding the use of gemini: https://support.google.com/gemini/answer/13594961\n"
            "2. You strictly control access via your own API Key.\n"
            "3. History is maintained only in your temporary session memory.\n"
            "4. No chat data or other personal information is persistently stored on my server (VPS). My data privacy declaration can be checked under: https://bautomate.dev/#legal" 
            )
        
        st.subheader("2) Sectionproperties", help="Check capabilites and assumptions under: https://sectionproperties.readthedocs.io/en/stable/")
        st.info("sectionproperties is an awesome and open-source python package for the analysis of arbitrary cross-sections using 2D finite elements. sectionproperties can be used to determine section properties to be used in structural design and visualise cross-sectional stresses resulting from arbitrary loading."
        )
    
        st.subheader("Tools used this session:", help="The LLM can only use specific tools that are declared in the tool_declaration.json file:\n - steel_sections: Different standard steel section generators from sectionproperties.\n - calculate_geometric_properties: Calculate geometric properties of the section.\n - calculate_warping_properties: Calculate warping properties of the section.\n - calculate_stress: Calculate stresses for given loading conditions.\n - plot_stress: Plot the calculated stresses over the section.")
        tool_history_placeholder = st.empty()
        with tool_history_placeholder.container():
            if 'tool_calls' in st.session_state and st.session_state.tool_calls:
                history_html = "".join([f"<div style='font-size: small; color: #808080; margin-bottom: 2px;'>{call}</div>" for call in st.session_state.tool_calls])
                st.markdown(history_html, unsafe_allow_html=True)
            else:
                st.caption("No tools called yet.")

    api_key = user_api_key 

    if not api_key or api_key == "xxx":
        st.warning("⚠️ To use this application, please enter your Google API Key in the sidebar.")
        st.stop()

    client = genai.Client(api_key=api_key)

    # Define the model you are going to use
    model_id =  "gemini-2.5-flash"
    #model_id =  "gemini-2.5-flash-lite"   

    # Generation Config
    config = GenerateContentConfig(
        system_instruction="You are a helpful assistant that uses specific functions to analyse sections. If a suitable function is found but not all required parameters are provided, ask the user for the missing parameters or propose defaults. Never blindly guess parameters and move forward without confirmation. Also describe the function you are going to use. If a function call was detected, always provide text output to the user based on the function response.",
        tools=[{"function_declarations": tools}],
    )

    # example prompts 
    # Generate a channel section with a depth of 250 mm, a width of 90 mm, a flange thickness of 15 mm, a web thickness of 8 mm, a corner radius of 12 mm and 8 elements over the radius. Calculate the section properties and print them.
    # please calculate the section properties.
    # please calculate stresses for Mxx = 5 kNm.
    # please plot the von mises stresses.

    # I want to analyse an i section, please assume some default parameters for demo purposes
    # please calculate all properties, calculate stresses for Mxx = 2 kNm and plot the von mises stresses

    st.title("Sectionproperties assistant 🤖")

    USER_AVATAR = "👤"
    BOT_AVATAR = "🤖"
    USER_AVATAR = None
    BOT_AVATAR = None

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'history' not in st.session_state:
        st.session_state.history = []

    if 'sec' not in st.session_state:
        st.session_state.sec = None

    if 'geom' not in st.session_state:
        st.session_state.geom = None

    if 'stresses' not in st.session_state:
        st.session_state.stresses = None

    if 'tool_calls' not in st.session_state:
            st.session_state.tool_calls = []
    
    # Display chat messages
    for message in st.session_state.messages:
        avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            if message["type"] == "text":
                st.markdown(message["content"])
            else:
                st.pyplot(message["content"], use_container_width=False)

    if not st.session_state.messages:
        introduction = "This is an app build around sectionproperties to analyse sections. How can I help you?"
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            st.write_stream(stream_data(introduction))
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": introduction})

    if user_prompt := st.chat_input("Awaiting input..."):
        st.session_state.messages.append({"role": "user", "type": "text", "content": user_prompt})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(user_prompt)

        with st.chat_message("assistant", avatar=BOT_AVATAR):
            with st.spinner("Thinking..."):
                st.session_state.history, st.session_state.sec, st.session_state.geom, st.session_state.stresses, figures = call_LLM(
                    client, model_id, config, user_prompt, st.session_state.history, st.session_state.tool_calls, tool_history_placeholder, st.session_state.sec, st.session_state.geom, st.session_state.stresses
                )
            
            message_placeholder = st.empty()
            full_response = f"{st.session_state.history[-1].parts[0].text}"
            message_placeholder.write_stream(stream_data(full_response))
            if figures:
                for fig in figures:
                    st.pyplot(fig, use_container_width = False)
                    print(fig.get_size_inches())
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": full_response})
        if figures:
            for fig in figures:
                st.session_state.messages.append({"role": "assistant", "type": "figure", "content": fig})

if __name__ == "__main__":
    main()
