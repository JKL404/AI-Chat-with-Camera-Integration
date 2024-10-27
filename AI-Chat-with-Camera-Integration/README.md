# AI Chat with Camera Integration

This project is a Streamlit application that integrates AI chat capabilities with a camera feed. It allows users to interact with an AI model using text or voice input and receive responses in both text and audio formats. The application also supports multiple languages and voice selections.

## Features

- **Camera Integration**: Start and stop the camera feed directly from the application.
- **Voice Input**: Use your microphone to input queries.
- **Text Input**: Type your queries directly into the chat interface.
- **Language Support**: Choose from multiple languages for input and output.
- **Voice Selection**: Select from a variety of voices for audio responses.
- **LLM Service Selection**: Choose between different LLM services for generating responses.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/JKL404/AI-Chat-with-Camera-Integration.git
   ```
2. Navigate to the project directory:
   ```bash
   cd AI-Chat-with-Camera-Integration
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables

Create a `.env` file in the root of your project directory and add the following keys:
```plaintext
ELEVENLABS_API_KEY="your_elevenlabs_api_key"
GROQ_API_KEY="your_groq_api_key"
```

Replace `"your_elevenlabs_api_key"` and `"your_groq_api_key"` with your actual API keys.

## Usage

Run the application using Streamlit:
```bash
streamlit run app.py
```

## Image

![Application Screenshot](talk-to-me/screenshots/image1.png)
![Application Screenshot](talk-to-me/screenshots/image2.png)

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Additional Information

### Supported Languages and Voices

The application supports multiple languages including English, Nepali, Hindi, and French. You can select your preferred language from the sidebar. Additionally, a variety of voices are available for audio responses, which can also be selected from the sidebar. This feature allows users to tailor the application to their linguistic and auditory preferences.

### LLM Service Options

You can choose between different LLM services such as Groq and Anthropic for generating AI responses. This selection can be made from the sidebar under the "LLM Service Selection" section. Different services may offer varying response styles or capabilities, so users can experiment to find the best fit for their needs.

### Camera and Chat Functionality

- **Camera**: The camera can be started and stopped using the controls in the sidebar. The feed is displayed in the sidebar when active, allowing users to see what the AI is "seeing" and potentially use this visual input in their queries.
- **Chat**: The chat interface allows for both text and voice input. Voice input can be activated by clicking the "Speak" button, which will record and transcribe your speech. This dual input method ensures flexibility in how users can interact with the AI.

### Troubleshooting

- Ensure that your camera and microphone permissions are enabled for the application.
- If the application does not start, check that all dependencies are installed correctly and that your API keys are set in the `.env` file.
