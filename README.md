# Sectionproperties AI Assistant 🤖

This Streamlit application acts as an intelligent interface for the [sectionproperties](https://sectionproperties.readthedocs.io/) Python library. It leverages Google's Gemini models to generate geometry, mesh sections, calculate structural properties, and visualize stresses through natural language commands. It's the result of first experimentations with toolcalling - it does by no means represent a meaningful or polished programm.

## Features

- **Natural Language Interface**: Chat with the assistant to define sections and analyses.
- **Section Generation**: Create standard steel sections (I-beams, Channels, box girders, etc.) or custom geometries.
- **Analysis**:
  - Calculate geometric properties (Area, Moment of Inertia, etc.).
  - Calculate warping properties.
  - Perform stress analysis (Axial, Bending, Shear, Torsion).
- **Visualization**: View generated meshes and stress plots directly in the chat.
- **Tool History**: Track exact function calls and parameters used by the AI.

## Prerequisites

- Python 3.9+
- A Google AI Studio API Key (Get one [here](https://aistudio.google.com/))

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/sectionprops-assistant.git
   cd sectionprops-assistant
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   pip install streamlit google-genai sectionproperties matplotlib numpy python-dotenv
   ```

## Usage

1. **Run the Streamlit app:**
   ```bash
   streamlit run main_streamlit.py
   ```

2. **Configure API Key:**
   - Enter your Google API Key in the sidebar input field.
   - Alternatively, create a `.env` file in the root directory with `GEMINI_API_KEY=your_key_here`.

3. **Start Chatting:**
   Type your requests in the chat input.

   **Example Prompts:**
   > "Generate a channel section with a depth of 250 mm, a width of 90 mm, a flange thickness of 15 mm, a web thickness of 8 mm, a corner radius of 12 mm and 8 elements over the radius."
   
   > "Calculate geometric and warping properties."
   
   > "Calculate stresses for a bending moment Mxx = 10 kNm and an axial force N = -50 kN."
   
   > "Plot the von Mises stress distribution."

   > "What tasks can you help me with?"

4. **Verify and Validate:**
   This tool is experimental. LLMs can make stuff up so please verify the tools called and the adopted arguments.  

## Privacy & Security

- This app acts as a UI wrapper. Your prompts are sent to Google's GenAI servers so I'd recommend to not share personal or proprietary information.
- Use your own API key to control access and quotas (there should be free tiers for testing).
- No chat history is persistently stored on the hosting server; session memory is temporary.

## Disclaimer

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## License

This project is open-source. Please refer to the license file for details.
