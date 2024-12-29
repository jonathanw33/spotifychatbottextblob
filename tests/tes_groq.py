from groq import Groq
import os

def test_groq():
    try:
        client = Groq(api_key='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')
        
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",  # One of their fastest models
            messages=[
                {"role": "system", "content": "You are a friendly music enthusiast."},
                {"role": "user", "content": "Say hello!"}
            ]
        )
        
        print("Response:", completion.choices[0].message.content)
        return True, "Groq setup successful!"
    except Exception as e:
        return False, f"Error setting up Groq: {str(e)}"

# Run test
success, message = test_groq()
print(message)