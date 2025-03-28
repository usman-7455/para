import os
import json
import random
import re
import csv
import streamlit as st

class BatchLearningParaphraser:
    def __init__(self, knowledge_file='synonym_knowledge.json'):
        """
        Initialize the paraphraser with batch learning capabilities
        
        Args:
            knowledge_file (str): File to store and load learned synonyms
        """
        self.knowledge_file = knowledge_file
        self.synonyms = self._load_knowledge()
        
        # Default base synonyms
        self.base_synonyms = {
            'make': ['create', 'construct', 'build', 'generate'],
            'say': ['state', 'mention', 'declare', 'express'],
            'go': ['travel', 'move', 'proceed', 'advance'],
            'get': ['obtain', 'receive', 'acquire', 'secure'],
            'take': ['grab', 'seize', 'collect', 'retrieve'],
        }
        
        # Merge base synonyms with learned synonyms
        for key, value in self.base_synonyms.items():
            if key not in self.synonyms:
                self.synonyms[key] = value
    
    def _load_knowledge(self):
        """
        Load existing synonym knowledge from file
        
        Returns:
            dict: Stored synonym dictionary
        """
        try:
            if os.path.exists(self.knowledge_file):
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            st.error(f"Error loading knowledge: {e}")
            return {}
    
    def _save_knowledge(self):
        """
        Save current synonym knowledge to file
        """
        try:
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.synonyms, f, indent=4, ensure_ascii=False)
        except Exception as e:
            st.error(f"Error saving knowledge: {e}")
    
    def batch_learn_synonyms(self, file_path):
        """
        Learn synonyms from a CSV or TXT file
        
        Args:
            file_path (str): Path to the uploaded file
        
        Returns:
            tuple: (total_words_learned, new_words_learned)
        """
        total_words = 0
        new_words = 0
        
        try:
            # Determine file type
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.csv':
                # Read CSV file
                with open(file_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        if len(row) >= 2:
                            self._add_synonym(row[0].lower(), row[1].lower())
                            total_words += 1
                            new_words += 1
            
            elif file_extension in ['.txt', '.tsv']:
                # Read TXT or TSV file
                with open(file_path, 'r', encoding='utf-8') as txtfile:
                    for line in txtfile:
                        # Split line by tab or comma
                        parts = re.split(r'[,\t]', line.strip())
                        if len(parts) >= 2:
                            self._add_synonym(parts[0].lower(), parts[1].lower())
                            total_words += 1
                            new_words += 1
            
            # Save the updated knowledge
            self._save_knowledge()
            
            return total_words, new_words
        
        except Exception as e:
            st.error(f"Error learning from file: {e}")
            return total_words, new_words
    
    def _add_synonym(self, word, synonym):
        """
        Add a single synonym to the knowledge base
        
        Args:
            word (str): Original word
            synonym (str): Synonym to add
        """
        # Ensure the word exists in synonyms
        if word not in self.synonyms:
            self.synonyms[word] = []
        
        # Add synonym only if it's not already present
        if synonym not in self.synonyms[word]:
            self.synonyms[word].append(synonym)
    
    def paraphrase(self, text, num_variations=3):
        """
        Generate paraphrased variations of input text
        
        Args:
            text (str): Input text to paraphrase
            num_variations (int): Number of paraphrase variations to generate
        
        Returns:
            list: Paraphrased text variations
        """
        # Tokenize the text into words
        words = re.findall(r'\b\w+\b', text)
        
        variations = []
        for _ in range(num_variations):
            # Create a copy of words to modify
            modified_words = words.copy()
            
            # Randomly replace some words with synonyms
            for i in range(len(modified_words)):
                if random.random() < 0.3:  # 30% chance of replacement
                    current_word = modified_words[i].lower()
                    
                    # Find synonyms (learned or base)
                    synonyms = self.synonyms.get(current_word, [current_word])
                    
                    # If no synonyms, use the original word
                    if synonyms:
                        modified_words[i] = random.choice(synonyms)
            
            # Reconstruct the paraphrased text
            paraphrased = ' '.join(modified_words)
            variations.append(paraphrased)
        
        return variations

def main():
    """
    Streamlit application for batch learning paraphraser
    """
    st.set_page_config(page_title="Batch Learning Paraphraser", page_icon="🧠")
    
    # Initialize paraphraser
    paraphraser = BatchLearningParaphraser()
    
    # Main title
    st.title('🧠 Batch Learning Paraphraser')
    
    # Tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["Paraphrase", "Batch Learn Synonyms", "View Knowledge"])
    
    with tab1:
        st.header("Paraphrase Text")
        # Input text
        input_text = st.text_area('Enter text to paraphrase', height=200, key="paraphrase_input")
        
        # Number of variations
        num_variations = st.slider(
            'Number of paraphrase variations', 
            min_value=1, 
            max_value=5,
            value=3,
            key="variation_slider"
        )
        
        if st.button('Paraphrase', key="paraphrase_button"):
            if input_text:
                try:
                    # Generate paraphrases
                    paraphrases = paraphraser.paraphrase(
                        input_text, 
                        num_variations=num_variations
                    )
                    
                    # Display results
                    st.subheader('Paraphrased Variations:')
                    for i, para in enumerate(paraphrases, 1):
                        st.text_area(f'Variation {i}', para, height=100)
                
                except Exception as e:
                    st.error(f'Error generating paraphrases: {e}')
            else:
                st.warning('Please enter some text to paraphrase')
    
    with tab2:
        st.header("Batch Learn Synonyms")
        st.markdown("""
        Upload a CSV or TXT file with synonyms.
        
        File Format:
        - CSV: word,synonym
        - TXT/TSV: word[tab/comma]synonym
        
        Example:
        ```
        happy,joyful
        big,large
        go,travel
        ```
        """)
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a CSV or TXT file", 
            type=['csv', 'txt', 'tsv']
        )
        
        if uploaded_file is not None:
            # Save the uploaded file temporarily
            with open("temp_synonym_file", 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            # Learn from the file
            total_words, new_words = paraphraser.batch_learn_synonyms("temp_synonym_file")
            
            # Remove temporary file
            os.remove("temp_synonym_file")
            
            # Display learning results
            st.success(f"Learned {new_words} new synonyms out of {total_words} total words")
    
    with tab3:
        # Display current knowledge
        st.header("Synonym Knowledge")
        st.json(paraphraser.synonyms)

if __name__ == '__main__':
    main()

# Example synonym file content (synonyms.csv)
"""
happy,joyful
happy,cheerful
big,large
big,huge
go,travel
go,move
say,speak
say,tell
"""