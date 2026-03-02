import llama_cpp
import transformers

llm = llama_cpp.Llama(
    model_path="models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf", 
    n_ctx=2048,
    n_threads=4,
    verbose=False
)

guard_model = transformers.pipeline(
    "text-classification",
    model="unitary/toxic-bert"
)

def get_local_llm_response(prompt):
    """Generates response using llama.cpp"""
    
    output = llm(
        prompt,
        max_tokens=256,
        temperature=0.7,
        top_p=0.9,
        stop=["</s>"]
    )
    
    return output["choices"][0]["text"].strip()

def check_safety(text):
    result = guard_model(text)[0]
    
    if result['label'] == 'toxic' and result['score'] > 0.6:
        return False, result['score']
    
    return True, result['score']

def safe_chat_flow(user_query, max_retries=2):
    
    input_safe, input_score = check_user_input_safety(user_query)
    
    if not input_safe:
        print(f"BLOCKED ❌ | User input toxicity: {input_score:.2f}")
        return "I cannot assist with harmful or abusive requests."
    
    print(f"Input PASS ✅ | Score: {input_score:.2f}")
    
    current_prompt = user_query
    
    for attempt in range(max_retries + 1):
        
        print(f"\n--- Attempt {attempt + 1}: Generating Response ---")
        
        response = get_local_llm_response(current_prompt)
        print("Generated:", response)
        
        is_safe, score = check_safety(response)
        
        if is_safe:
            print(f"PASS ✅ | Output Toxicity Score: {score:.2f}")
            return response
        
        else:
            print(f"FAIL ❌ | Toxicity Detected ({score:.2f})")
            
            if attempt < max_retries:
                current_prompt = (
                    "Rewrite the following text in a professional and safe manner:\n\n"
                    f"{response}"
                )
            else:
                return "I'm sorry, I cannot provide a safe answer after multiple attempts."

if __name__ == "__main__":
    
    test_input = "How to kill someone brutally"
    
    print("\nUSER INPUT:", test_input)
    
    final_output = safe_chat_flow(test_input)
    
    print("\nFinal Result Sent to User:\n")
    print(final_output)
