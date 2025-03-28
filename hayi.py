import os
import json
import random
import re
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from difflib import SequenceMatcher
from nltk.corpus import wordnet
import nltk

class BatchLearningParaphraser:
    def __init__(self, knowledge_file='synonym_knowledge.json'):
        # Initialize NLTK
        try:
            nltk.data.find('corpora/wordnet')
        except:
            nltk.download('wordnet')
        
        self.use_nltk = True  # Toggle for NLTK integration
        self.synonym_confidence = 0.8  # Threshold for NLTK synonym similarity
        self.knowledge_file = knowledge_file
        self.synonyms = self._load_knowledge()
        self.newly_added_synonyms = {}
        
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

    def _get_nltk_synonyms(self, word):
        """Fetch synonyms from WordNet with similarity filtering."""
        synonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonym = lemma.name().replace("_", " ").lower()
                if synonym != word and synonym.isalpha():
                    # Filter by similarity to original word
                    similarity = SequenceMatcher(None, word, synonym).ratio()
                    if similarity >= self.synonym_confidence:
                        synonyms.add(synonym)
        return list(synonyms)
    
    def _load_knowledge(self):
        try:
            if os.path.exists(self.knowledge_file):
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            messagebox.showerror("Error", f"Error loading knowledge: {e}")
            return {}
    
    def _save_knowledge(self):
        try:
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.synonyms, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Error saving knowledge: {e}")
    
    def batch_learn_synonyms(self, file_path):
        total_words = 0
        new_words = 0
        self.newly_added_synonyms = {}
        
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            word = row[0].lower()
                            synonym = row[1].lower()
                            self._add_synonym(word, synonym)
                            total_words += 1
                            new_words += 1
            else:  # for .txt and .tsv
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = re.split(r'[,\t]', line.strip())
                        if len(parts) >= 2:
                            word = parts[0].lower()
                            synonym = parts[1].lower()
                            self._add_synonym(word, synonym)
                            total_words += 1
                            new_words += 1
            
            self._save_knowledge()
            return total_words, new_words
        
        except Exception as e:
            messagebox.showerror("Error", f"Error learning from file: {e}")
            return total_words, new_words
    
    def _add_synonym(self, word, synonym):
        if word not in self.synonyms:
            self.synonyms[word] = []
        
        if synonym not in self.synonyms[word]:
            self.synonyms[word].append(synonym)
            
            if word not in self.newly_added_synonyms:
                self.newly_added_synonyms[word] = []
            self.newly_added_synonyms[word].append(synonym)
        
        if synonym not in self.synonyms:
            self.synonyms[synonym] = []
        
        if word not in self.synonyms[synonym]:
            self.synonyms[synonym].append(word)
            
            if synonym not in self.newly_added_synonyms:
                self.newly_added_synonyms[synonym] = []
            self.newly_added_synonyms[synonym].append(word)

    def paraphrase(self, text, num_variations=3):
        words = re.findall(r'\b\w+\b', text)
        variations = []
        
        for _ in range(num_variations):
            modified_words = []
            changed_words = []
            
            for word in words:
                current_word = word.lower()
                
                # Combine learned synonyms + NLTK synonyms (if enabled)
                synonyms = [
                    syn for syn in self.synonyms.get(current_word, []) 
                    if syn != current_word
                ]
                
                if self.use_nltk:
                    nltk_synonyms = self._get_nltk_synonyms(current_word)
                    synonyms.extend(s for s in nltk_synonyms if s not in synonyms)
                
                if synonyms:
                    new_word = random.choice(synonyms)
                    modified_words.append(new_word)
                    changed_words.append({
                        'original': word,
                        'new': new_word,
                        'position': len(modified_words) - 1,
                        'source': 'NLTK' if (self.use_nltk and new_word in nltk_synonyms) else 'Learned'
                    })
                else:
                    modified_words.append(word)
            
            paraphrased_text = ' '.join(modified_words)
            variations.append((paraphrased_text, changed_words))
        
        return variations


class ParaphraserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Learning Paraphraser")
        self.root.geometry("1000x750")
        self.root.minsize(800, 600)
        
        # Set theme colors
        self.bg_color = "#f5f5f5"
        self.primary_color = "#4a6fa5"
        self.secondary_color = "#166088"
        self.highlight_color = "#ffd700"
        
        # Configure styles
        self._configure_styles()
        
        self.paraphraser = BatchLearningParaphraser()
        
        # Create main container
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create status bar FIRST
        self.status_bar = ttk.Label(
            root, 
            text="Ready", 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            style='Status.TLabel'
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill='both', expand=True)
        
        # Create frames for each tab
        self.paraphrase_frame = ttk.Frame(self.notebook)
        self.learn_frame = ttk.Frame(self.notebook)
        self.knowledge_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.paraphrase_frame, text=' Paraphrase ')
        self.notebook.add(self.learn_frame, text=' Batch Learn ')
        self.notebook.add(self.knowledge_frame, text=' View Knowledge ')
        
        # Build each tab
        self._build_paraphrase_tab()
        self._build_learn_tab()
        self._build_knowledge_tab()
    
    def _configure_styles(self):
        style = ttk.Style()
        
        # Configure main styles
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TNotebook', background=self.bg_color)
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'))
        
        # Custom styles
        style.configure('Primary.TButton', 
                       foreground='white', 
                       background=self.primary_color,
                       font=('Segoe UI', 10, 'bold'))
        
        style.configure('Highlight.TFrame', 
                       background=self.highlight_color,
                       relief=tk.RAISED,
                       borderwidth=1)
        
        style.configure('Status.TLabel', 
                       background='#e0e0e0',
                       font=('Segoe UI', 9))
        
        style.map('Primary.TButton',
                 background=[('active', self.secondary_color)])
        
        # Configure scrollbars
        style.configure('Vertical.TScrollbar', 
                        arrowsize=14,
                        gripcount=0,
                        background='#d0d0d0',
                        troughcolor=self.bg_color,
                        arrowcolor='white')
        
        style.configure('Horizontal.TScrollbar', 
                       arrowsize=14,
                       gripcount=0,
                       background='#d0d0d0',
                       troughcolor=self.bg_color,
                       arrowcolor='white')
    
    def _build_paraphrase_tab(self):
        # Main content frame with scrollbar
        self.paraphrase_canvas = tk.Canvas(
            self.paraphrase_frame, 
            bg=self.bg_color,
            highlightthickness=0
        )
        self.paraphrase_scrollbar = ttk.Scrollbar(
            self.paraphrase_frame, 
            orient=tk.VERTICAL, 
            command=self.paraphrase_canvas.yview,
            style='Vertical.TScrollbar'
        )
        self.paraphrase_scrollable_frame = ttk.Frame(self.paraphrase_canvas)
        
        self.paraphrase_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.paraphrase_canvas.configure(
                scrollregion=self.paraphrase_canvas.bbox("all")
            )
        )
        
        self.paraphrase_canvas.create_window(
            (0, 0), 
            window=self.paraphrase_scrollable_frame, 
            anchor="nw"
        )
        self.paraphrase_canvas.configure(yscrollcommand=self.paraphrase_scrollbar.set)
        
        self.paraphrase_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.paraphrase_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure mousewheel scrolling
        self.paraphrase_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # NLTK Settings Frame
        nltk_frame = ttk.Frame(self.paraphrase_scrollable_frame)
        nltk_frame.pack(fill=tk.X, padx=5, pady=5)

        # Toggle for NLTK
        self.use_nltk = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            nltk_frame, 
            text="Use NLTK Synonyms", 
            variable=self.use_nltk,
            command=lambda: setattr(self.paraphraser, 'use_nltk', self.use_nltk.get())
        ).pack(side=tk.LEFT, padx=5)

        # Confidence Threshold Slider
        ttk.Label(nltk_frame, text="Synonym Match:").pack(side=tk.LEFT, padx=5)
        self.confidence = tk.DoubleVar(value=0.8)
        ttk.Scale(
            nltk_frame,
            from_=0.1,
            to=1.0,
            variable=self.confidence,
            command=lambda v: setattr(self.paraphraser, 'synonym_confidence', float(v))
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Input section
        input_frame = ttk.LabelFrame(
            self.paraphrase_scrollable_frame, 
            text="Input Text",
            padding=(10, 5)
        )
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Enter text to paraphrase:").pack(anchor=tk.W)
        
        self.input_text = scrolledtext.ScrolledText(
            input_frame, 
            width=80, 
            height=10,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            padx=5,
            pady=5
        )
        self.input_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Settings section
        settings_frame = ttk.Frame(self.paraphrase_scrollable_frame)
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(settings_frame, text="Number of variations:").pack(side=tk.LEFT, padx=5)
        self.num_variations = tk.IntVar(value=3)
        ttk.Spinbox(
            settings_frame, 
            from_=1, 
            to=5, 
            textvariable=self.num_variations,
            width=5,
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # Paraphrase button
        ttk.Button(
            settings_frame, 
            text="Generate Paraphrases", 
            command=self._generate_paraphrases,
            style='Primary.TButton'
        ).pack(side=tk.RIGHT, padx=5)
        
        # Results section
        self.results_frame = ttk.Frame(self.paraphrase_scrollable_frame)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _on_mousewheel(self, event):
        self.paraphrase_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _generate_paraphrases(self):
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text to paraphrase")
            return
        
        try:
            num_variations = self.num_variations.get()
            paraphrases = self.paraphraser.paraphrase(text, num_variations)
            
            if not paraphrases:
                ttk.Label(
                    self.results_frame, 
                    text="No paraphrases could be generated with current knowledge.",
                    foreground="red"
                ).pack(pady=10)
                return
            
            for i, (para, changed_words) in enumerate(paraphrases, 1):
                # Create a frame for each variation
                var_frame = ttk.LabelFrame(
                    self.results_frame, 
                    text=f"Variation {i}",
                    padding=(10, 5),
                    style='Highlight.TFrame'
                )
                var_frame.pack(fill=tk.X, padx=5, pady=5, ipady=5)
                
                # Display highlighted text
                text_widget = tk.Text(
                    var_frame, 
                    width=80, 
                    height=4,
                    wrap=tk.WORD,
                    font=('Segoe UI', 10),
                    padx=5,
                    pady=5,
                    relief=tk.FLAT,
                    bg='white'
                )
                text_widget.pack(fill=tk.X, padx=5, pady=5)
                
                # Insert text with highlighting for changed words
                para_words = para.split()
                for j, word in enumerate(para_words):
                    is_changed = any(chg['position'] == j for chg in changed_words)
                    if is_changed:
                        text_widget.insert(tk.END, word + ' ', 'highlight')
                    else:
                        text_widget.insert(tk.END, word + ' ')
                
                text_widget.tag_configure('highlight', 
                                        background=self.highlight_color,
                                        font=('Segoe UI', 10, 'bold'))
                text_widget.config(state=tk.DISABLED)
                
                # Show changes in an expandable section
                changes_frame = ttk.Frame(var_frame)
                changes_frame.pack(fill=tk.X, padx=5, pady=5)
                
                show_btn = ttk.Button(
                    changes_frame, 
                    text="Show Changes", 
                    command=lambda c=changed_words, f=changes_frame: self._show_changes(c, f),
                    style='Primary.TButton'
                )
                show_btn.pack(side=tk.LEFT)
                
                # Add separator
                ttk.Separator(self.results_frame).pack(fill=tk.X, pady=5)
            
            self.status_bar.config(text="Paraphrases generated successfully")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error generating paraphrases: {e}")
            self.status_bar.config(text="Error generating paraphrases")
    
    def _show_changes(self, changed_words, frame):
        # Clear the frame
        for widget in frame.winfo_children():
            widget.destroy()
        
        if changed_words:
            changes_text = tk.Text(
                frame, 
                width=80, 
                height=min(10, len(changed_words) + 1),
                wrap=tk.WORD,
                font=('Segoe UI', 9),
                padx=5,
                pady=5,
                relief=tk.FLAT,
                bg='white'
            )
            changes_text.pack(fill=tk.X, padx=5, pady=5)
            
            changes_text.insert(tk.END, "Changed words:\n")
            for change in changed_words:
                changes_text.insert(tk.END, f"• '{change['original']}' → '{change['new']}' (Source: {change['source']})\n")
            
            changes_text.tag_add("title", "1.0", "1.13")
            changes_text.tag_config("title", font=('Segoe UI', 9, 'bold'))
            changes_text.config(state=tk.DISABLED)
        else:
            ttk.Label(
                frame, 
                text="No words were changed in this variation.",
                font=('Segoe UI', 9, 'italic')
            ).pack(anchor=tk.W)
    
    def _build_learn_tab(self):
        # Main content frame with scrollbar
        self.learn_canvas = tk.Canvas(
            self.learn_frame, 
            bg=self.bg_color,
            highlightthickness=0
        )
        self.learn_scrollbar = ttk.Scrollbar(
            self.learn_frame, 
            orient=tk.VERTICAL, 
            command=self.learn_canvas.yview,
            style='Vertical.TScrollbar'
        )
        self.learn_scrollable_frame = ttk.Frame(self.learn_canvas)
        
        self.learn_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.learn_canvas.configure(
                scrollregion=self.learn_canvas.bbox("all")
            )
        )
        
        self.learn_canvas.create_window(
            (0, 0), 
            window=self.learn_scrollable_frame, 
            anchor="nw"
        )
        self.learn_canvas.configure(yscrollcommand=self.learn_scrollbar.set)
        
        self.learn_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.learn_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Instructions section
        instructions_frame = ttk.LabelFrame(
            self.learn_scrollable_frame, 
            text="Instructions",
            padding=(10, 5)
        )
        instructions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        instructions = """Upload a CSV or TXT file with synonyms to expand the paraphraser's knowledge.

File Format:
- CSV: word,synonym
- TXT/TSV: word[tab/comma]synonym

Example:
happy,joyful
big,large
go,travel"""
        
        instruction_text = tk.Text(
            instructions_frame, 
            width=80, 
            height=8,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            padx=5,
            pady=5,
            relief=tk.FLAT,
            bg='white'
        )
        instruction_text.insert(tk.END, instructions)
        instruction_text.config(state=tk.DISABLED)
        instruction_text.pack(fill=tk.X, padx=5, pady=5)
        
        # File upload section
        upload_frame = ttk.Frame(self.learn_scrollable_frame)
        upload_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            upload_frame, 
            text="Select Synonym File", 
            command=self._select_file,
            style='Primary.TButton'
        ).pack(pady=10)
        
        # Results section
        self.learn_result = ttk.Label(
            self.learn_scrollable_frame, 
            text="",
            font=('Segoe UI', 10)
        )
        self.learn_result.pack(pady=5)
        
        # Newly added synonyms
        self.new_synonyms_frame = ttk.LabelFrame(
            self.learn_scrollable_frame, 
            text="Newly Added Synonyms",
            padding=(10, 5)
        )
        self.new_synonyms_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.new_synonyms_text = scrolledtext.ScrolledText(
            self.new_synonyms_frame, 
            width=80, 
            height=10,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            padx=5,
            pady=5,
            relief=tk.FLAT,
            bg='white'
        )
        self.new_synonyms_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.new_synonyms_text.config(state=tk.DISABLED)
    
    def _select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Synonym File",
            filetypes=[("CSV/TXT Files", "*.csv;*.txt;*.tsv"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                total_words, new_words = self.paraphraser.batch_learn_synonyms(file_path)
                self.learn_result.config(
                    text=f"Successfully learned {new_words} new synonyms out of {total_words} total words",
                    foreground="green"
                )
                
                # Display newly added synonyms
                self.new_synonyms_text.config(state=tk.NORMAL)
                self.new_synonyms_text.delete(1.0, tk.END)
                
                if self.paraphraser.newly_added_synonyms:
                    self.new_synonyms_text.insert(
                        tk.END, 
                        json.dumps(self.paraphraser.newly_added_synonyms, indent=2)
                    )
                else:
                    self.new_synonyms_text.insert(tk.END, "No new synonyms were added.")
                
                self.new_synonyms_text.config(state=tk.DISABLED)
                
                # Refresh knowledge tab
                self._refresh_knowledge_tab()
                
                self.status_bar.config(text=f"Loaded synonyms from {os.path.basename(file_path)}")
            
            except Exception as e:
                self.learn_result.config(
                    text=f"Error processing file: {str(e)}",
                    foreground="red"
                )
                self.status_bar.config(text="Error loading synonym file")
    
    def _build_knowledge_tab(self):
        # Main content frame with scrollbar
        self.knowledge_canvas = tk.Canvas(
            self.knowledge_frame, 
            bg=self.bg_color,
            highlightthickness=0
        )
        self.knowledge_scrollbar = ttk.Scrollbar(
            self.knowledge_frame, 
            orient=tk.VERTICAL, 
            command=self.knowledge_canvas.yview,
            style='Vertical.TScrollbar'
        )
        self.knowledge_scrollable_frame = ttk.Frame(self.knowledge_canvas)
        
        self.knowledge_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.knowledge_canvas.configure(
                scrollregion=self.knowledge_canvas.bbox("all")
            )
        )
        
        self.knowledge_canvas.create_window(
            (0, 0), 
            window=self.knowledge_scrollable_frame, 
            anchor="nw"
        )
        self.knowledge_canvas.configure(yscrollcommand=self.knowledge_scrollbar.set)
        
        self.knowledge_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.knowledge_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Controls frame
        controls_frame = ttk.Frame(self.knowledge_scrollable_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            controls_frame, 
            text="Refresh Knowledge", 
            command=self._refresh_knowledge_tab,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            controls_frame, 
            text="Export Knowledge", 
            command=self._export_knowledge,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        # Knowledge display
        self.knowledge_text = scrolledtext.ScrolledText(
            self.knowledge_scrollable_frame, 
            width=80, 
            height=20,
            wrap=tk.WORD,
            font=('Segoe UI', 10),
            padx=5,
            pady=5,
            relief=tk.FLAT,
            bg='white'
        )
        self.knowledge_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load initial knowledge
        self._refresh_knowledge_tab()
    
    def _refresh_knowledge_tab(self):
        self.knowledge_text.config(state=tk.NORMAL)
        self.knowledge_text.delete(1.0, tk.END)
        
        if self.paraphraser.synonyms:
            self.knowledge_text.insert(
                tk.END, 
                json.dumps(self.paraphraser.synonyms, indent=2)
            )
        else:
            self.knowledge_text.insert(tk.END, "No synonyms have been learned yet.")
        
        self.knowledge_text.config(state=tk.DISABLED)
        self.status_bar.config(text="Knowledge base refreshed")
    
    def _export_knowledge(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Save Knowledge Base As"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.paraphraser.synonyms, f, indent=2)
                
                messagebox.showinfo("Success", "Knowledge base exported successfully")
                self.status_bar.config(text=f"Knowledge exported to {os.path.basename(file_path)}")
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export knowledge: {str(e)}")
                self.status_bar.config(text="Error exporting knowledge")

if __name__ == '__main__':
    # Initialize the main application window
    root = tk.Tk()
    root.title("Batch Learning Paraphraser")
    
    # Set window icon (handles cases where icon might not be available)
    try:
        root.iconbitmap('paraphraser.ico')  # Windows .ico format
    except:
        try:
            # Try alternative icon formats for other platforms
            img = tk.PhotoImage(file='paraphraser.png')
            root.iconphoto(True, img)
        except:
            pass  # Continue without icon if none available
    
    # Configure initial window size and minimum size
    root.geometry("1000x750")
    root.minsize(800, 600)
    
    # Create and run the application
    app = ParaphraserApp(root)
    
    # Center the window on screen
    root.eval('tk::PlaceWindow . center')
    
    # Start the main event loop
    root.mainloop()