<img src="https://mintlify.s3-us-west-1.amazonaws.com/duohub/logo/logo-light.svg" alt="duohub logo" height="20"> &nbsp;
<img src="https://mintlify.s3-us-west-1.amazonaws.com/daily/logo/dark.svg" alt="pipecat logo" height="20">


# duohub x Pipecat graph memory integration example

This example shows how to use the duohub graph memory integration with the pipecat framework for voice AI. 

It uses: 

- OpenAI for the LLM
- Cartesia for the TTS
- Daily for the audio call
- duohub for the graph memory integration

Dependencies are managed with Poetry. The project can be containerised with Docker and deployed on ECS.

## Running the example

To run the example, follow these steps:

1. Clone the repository
2. Install dependencies with `poetry install`
3. Set the environment variables in the `.env` file
4. Run the example with `poetry run python server.py`
5. Go to [http://0.0.0.0:7860](http://0.0.0.0:7680) in your browser
6. Check the logs in the terminal to see duohub memory in action

## Requirements

- Python 3.12
- Poetry
- Docker
- [Cartesia API key](https://cartesia.ai/sonic)
- [Daily API key](https://daily.co/developers)
- [OpenAI API key](https://platform.openai.com/api-keys)
- [duohub API key](https://app.duohub.ai/account)