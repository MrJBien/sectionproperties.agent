import os
import json
from dotenv import load_dotenv

from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig

from sectionproperties.pre.library import circular_hollow_section, elliptical_hollow_section, rectangular_hollow_section, polygon_hollow_section, i_section, mono_i_section, tapered_flange_i_section, channel_section, tapered_flange_channel, tee_section, angle_section, cee_section, zed_section, box_girder_section, bulb_section
from sectionproperties.analysis import Section


with open("tool_declaration.json", 'r') as f:
    tools = json.load(f)


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


def call_LLM(client, model_id, config, user_prompt, history, sec=None, geom=None, stresses=None):

    history.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))

    response = client.models.generate_content(
        model=model_id,
        config=config,
        contents=history
    )

    # Collect all function calls in this turn
    nfunction_calls = 0
    function_calls = []
    for part in response.candidates[0].content.parts:

        # add response to the conversation
        history.append(types.Content(role="model", parts=[part]))
        # check if the response is a function call
        if part.function_call:
            nfunction_calls += 1
            print(f"function call {nfunction_calls}: {part.function_call.name} ")
            function_calls.append(part.function_call)
        # check if the response is regular text
        elif part.text:
            print(f"text response: {part.text}")
        else:
            print(f"Unhandled content part type: {type(part)}")     

    # Prepare all function response parts
    function_response_parts = []
    nfunction_response_part = 0
    for function_call in function_calls:            
        # Call the tool with arguments
        print(f"{"\033[90m"}logger: Calling tool {function_call.name} with args: {function_call.args}{"\033[0m"}\n")

        # For functions in the current global scope:
        if function_call.name in globals():
            func_obj = globals()[function_call.name]    
            srcmodule = func_obj.__module__ #module where the function is defined
        else:    
            srcmodule = None

        if srcmodule == "sectionproperties.pre.library.steel_sections":
            try:
                ele_size = 10
                geom = eval(call_function(function_call.name, **function_call.args))
                geom.create_mesh(mesh_sizes=ele_size)
                sec = Section(geometry=geom)
                sec.plot_mesh(materials=False, pause = False)
                #tool_result = {"description": f"Section of type {function_call.name} generated and meshed."}
                tool_result = {
                    "status": "success",
                    "message": f"Geometry of the section generated and meshed successfully. A default element size of {ele_size} mm was used.",
                    "next_steps_suggestion": "Would you like to evaluate the section properties or perform a stress analysis?"
                }
            except Exception as e:
                tool_result = {
                    "status": "error",
                    "message": f"Error calling {function_call.name}: {str(e)}"
                }
        elif function_call.name == "calculate_geometric_properties":
            try:
                eval(call_function(function_call.name, "sec", **function_call.args))
                for dicts in tools:
                    if dicts['name'] == function_call.name:
                        description = dicts['description']
                        break
                #tool_result = {"description": f"Geometric section properties have been calculated.", "section_props": sec.section_props}
                #tool_result = f"Function {function_call.name} with the following purpose: {description} executed successfully. Section properties are stored in {sec.section_props}" 
                tool_result = {
                    "status": "success",
                    "message": f"Geometric section properties have been calculated successfully.",
                    "section_properties": sec.section_props,
                    "next_steps_suggestion": "Would you like to calculate warping properties or perform a stress analysis?"
                }            
            except Exception as e:
                tool_result = {
                    "status": "error",
                    "message": f"Error calling {function_call.name}: {str(e)}"
                }
        elif function_call.name == "calculate_warping_properties":
            try:
                eval(call_function(function_call.name, "sec", **function_call.args))
                for dicts in tools:
                    if dicts['name'] == function_call.name:
                        description = dicts['description']
                        break
                #tool_result = {"description": f"Warping properties of the section have been calculated.", "warping_props": sec.section_props}
                #tool_result = f"Function {function_call.name} has been executed successfully. The purpose of the function is: {description}. Section properties are stored in {sec.section_props}" 
                tool_result = {
                    "status": "success",
                    "message": f"Warping properties of the section have been calculated successfully.",
                    "section_properties": sec.section_props,
                    "next_steps_suggestion": "Would you like to continue with a stress analysis?"
                }
            except Exception as e:
                tool_result = {
                    "status": "error",
                    "message": f"Error calling {function_call.name}: {str(e)}"
                }
        elif function_call.name == "calculate_stress":
            try:
                stresses = eval(call_function(function_call.name, "sec", **function_call.args))
                for dicts in tools:
                    if dicts['name'] == function_call.name:
                        description = dicts['description']
                        break
                tool_result = {
                    "status": "success",
                    "message": f"Section stresses have been calculated successfully.",
                    "next_steps_suggestion": "Would you like to view the stress results? I could plot the Axial, Shear or von Mises stresses for you.",
                }
                #tool_result = {"description": f"Stresses have been calculated for the section.", "axial_stresses": {stresses.material_groups[0].stress_result.sig_zz}, "shear_stresses": {stresses.material_groups[0].stress_result.sig_zxy}, "von_mises_stresses": {stresses.material_groups[0].stress_result.sig_vm}}
                #tool_result = f"Function {function_call.name} has been executed successfully. The purpose of the function is: {description}. Section stresses are stored in {stresses.material_groups[0].stress_result.sig_vm}."
            except Exception as e:
                tool_result = {
                    "status": "error",
                    "message": f"Error calling {function_call.name}: {str(e)}"
                }
        elif function_call.name == "plot_stress":
            try:
                eval(call_function(function_call.name, "stresses", **function_call.args, normalize=False, pause = False))
                for dicts in tools:
                    if dicts['name'] == function_call.name:
                        description = dicts['description']
                        break
                tool_result = {
                    "status": "success",
                    "message": f"Plot of {function_call.args.get('plot_type')} stresses generated.",
                    "plot_description": "A plot of the stresses over the section.",
                    "caption_suggestion": "Here's the section stress plot.",
                }
                #tool_result = f"Function {function_call.name} has been executed successfully. The purpose of the function is: {description}."
            except Exception as e:
                tool_result = {
                    "status": "error",
                    "message": f"Error calling {function_call.name}: {str(e)}"
                }
        # elif function_call.name == "GoogleSearch":
        #     search_response = client.models.generate_content(
        #         model=model_id,
        #         config = GenerateContentConfig(
        #             system_instruction="Perform an online search on basic section dimensions for standard steel sections in the web and output them in a structured way.",
        #             tools=[types.Tool(google_search=types.GoogleSearch())],                               
        #             ),
        #         contents=history
        #         )
        #     tool_result = search_response.candidates[0].content.parts[0].text
        
        nfunction_response_part += 1
        print(f"function response call {nfunction_response_part}: {tool_result}")
        function_response_part = types.Part.from_function_response(
            name=function_call.name,
            response=tool_result,
        )
        function_response_parts.append(function_response_part)

    if function_response_parts:
        history.append(types.Content(role="user", parts=function_response_parts))
        func_gen_response = client.models.generate_content(
            model=model_id, config=config, contents=history
        )
        history.append(types.Content(role="model", parts=[func_gen_response]))

    return history, sec if 'sec' in locals() else None, geom if 'geom' in locals() else None, stresses if 'stresses' in locals() else None


def main():
    # create client
    load_dotenv()  # take environment variables from .env.
    api_key = os.getenv("GEMINI_API_KEY","xxx")    
    client = genai.Client(api_key=api_key)

    # Define the model you are going to use
    #model_id =  "gemini-2.0-flash"
    #model_id =  "gemini-2.5-flash-lite-preview-06-17"
    model_id =  "gemini-2.5-flash"
    # Generation Config
    config = GenerateContentConfig(
        system_instruction="You are a helpful assistant that uses specific functions to analyse sections. If a suitable function is found but not all required parameters are provided, ask the user for the missing parameters or propose defaults. Also describe the function you are going to use. If a function call was detected, always provide text output to the user based on the function response.",
        tools=[{"function_declarations": tools}],
    )

    # example prompts 
    # Generate a channel section with a depth of 250 mm, a width of 90 mm, a flange thickness of 15 mm, a web thickness of 8 mm, a corner radius of 12 mm and 8 elements over the radius.
    # please calculate the section properties.
    # please calculate stresses for Mxx = 5 kNm.
    # please plot the von mises stresses.

    # I want to analyse an i section, please assume some default parameters for demo purposes
    # 
    # please calculate all properties, calculate stresses for Mxx = 2 kNm and plot the von mises stresses


    print(f"\n{"\033[94m"}model: This is an app build around sectionproperties to analyse sections. How can I help you? You can type 'q' to quit the app.{"\033[0m"}\n")
    history = []
    sec = None
    geom = None
    stresses = None
    user_prompt =""

    
    while True:
        user_prompt = input(f"{"\033[92m"}user: ")
        print(f"{"\033[0m"}{"\033[0m"}")
        if user_prompt == "q" or user_prompt == "quit" or user_prompt == "exit":
            print(f"{"\033[94m"}model: Exiting the app. Goodbye!{"\033[0m"}\n")
            break
        history, sec, geom, stresses = call_LLM(client, model_id, config, user_prompt, history, sec, geom, stresses)
        print(f"{"\033[94m"}model: {history[-1].parts[0].text}{"\033[0m"}")  # Print the latest response from the model

if __name__ == "__main__":
    main()
