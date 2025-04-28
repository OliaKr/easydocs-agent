
import os
from dotenv import load_dotenv
import chainlit as cl
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_API_VERSION")
)

cl.instrument_openai()

settings = {
    "model": os.getenv("AZURE_DEPLOYMENT_ID"),
    "temperature": 0,
}


@cl.on_message
async def on_message(message: cl.Message):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are EasyDocs, an assistant that simplifies legal and business documents into easy-to-read English or Hebrew."
            },
            {
                "role": "user",
                "content": message.content
            }
        ],
        **settings
    )
    await cl.Message(content=response.choices[0].message.content).send()
