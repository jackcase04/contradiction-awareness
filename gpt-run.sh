#!/bin/bash
set -e

for MODEL in llama3.2:latest gemma4:latest qwen3.5:latest; do
    for CONFIG in pre-prompt post-prompt; do
        for FILE in haystacks/*; do
            for I in {1..10}; do
            	
                  FILE_CONTENT=$(<$FILE) 
                  
                  echo $FILE
                  
                  if [[ $FILE == haystacks/biology_haystack.txt ]]; then
                  	QUESTION="USER INPUT: In which genus is Xaltruvia classified?"
                    DOMAIN=biology
                  elif [[ $FILE == haystacks/geography_haystack.txt ]]; then
                  	QUESTION="USER INPUT: What is the capital of Xaltruvia?"
                    DOMAIN=geography
                  elif [[ $FILE == haystacks/history_haystack.txt ]]; then
                  	QUESTION="USER INPUT: Which treaty resolved the Xaltruvian conflict?"
                    DOMAIN=history
                  fi
                  
                  
                  if [[ $CONFIG == control ]]; then
                  
                  	FILE_CONTENT="${FILE_CONTENT} ${QUESTION}"
                  
                  elif [[ $CONFIG == pre-prompt ]]; then
                    # We should consider changing the pre-prompt to this to use chain-of-thought reasoning:
                    # You are evaluating a passage for factual consistency. 
                    # Before forming any answer:
                    # - Extract every claim relevant to the question and list them
                    # - Check whether any extracted claims contradict each other
                    # - If contradictions exist, explicitly state them and do NOT resolve them, instead report the contradiction as your answer
                    # - Only if no contradictions exist, provide a confident answer
                  	FILE_CONTENT="${FILE_CONTENT} SYSTEM INPUT:Answer the following question by evaluating all of the relevant information. Produce the most likely answer, and explain any potential ambiguity caused by conflicting information in your sources. ${QUESTION}"
                    
                  fi
                  

                  PAYLOAD=$(jq -n \
                    --arg model "$MODEL" \
                    --arg prompt "$FILE_CONTENT" \
                    '{model: $model, prompt: $prompt, stream: false}')

                  echo $PAYLOAD

                  curl http://localhost:11434/api/generate -d "$PAYLOAD" | jq -r '.response' > results/${MODEL}_${CONFIG}_${DOMAIN}_trial${I}.txt
                
            done
        done
    done
done
