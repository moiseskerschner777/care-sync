from litellm import completion

response = completion(
    model="deepseek/deepseek-chat",
    messages=[
        {"role": "system", "content": "do you know what a dog is?"},
        {"role": "user", "content": "Hello!"}
    ],
    api_key="",
    api_base="https://api.deepseek.com"
)

# full response object
print(response)

# just the message
print(response["choices"][0]["message"]["content"])

# model used + tokens consumed
print("model:", response["model"])
print("tokens:", response["usage"])
