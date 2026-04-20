import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import argparse


class TSVAnnotator:
    def __init__(self, root, tsv_file):
        self.root = root
        self.root.title("GESIS Document Annotation Verification")
        #         self.root.geometry("1200x800")

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Use 80% of screen size
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)
        self.root.geometry(f"{window_width}x{window_height}")

        # File handling
        self.tsv_file = tsv_file
        # Read the file first to count columns
        with open(tsv_file, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            num_columns = len(first_line.split('\t'))

        if num_columns == 7:
            self.data = pd.read_csv(tsv_file, sep='\t', header=None,
                                    names=['QueryId', 'Query', 'QueryDesc', 'Docid', 'Abstract', 'Label', 'Annotation'])
        elif num_columns == 6:
            self.data = pd.read_csv(tsv_file, sep='\t', header=None,
                                    names=['QueryId', 'Query', 'QueryDesc', 'Docid', 'Abstract', 'Label'])
            self.data['Annotation'] = pd.NA
        else:
            raise ValueError(f"Unexpected number of columns: {num_columns}")

        #         self.data = pd.read_csv(tsv_file, sep='\t', header=None,
        #                                 names=['QueryId', 'Query', 'QueryDesc', 'Docid', 'Abstract', 'Label'])
        self.current_index = 0
        self.total_rows = len(self.data)

        # Add annotation column if not exists
        if 'Annotation' not in self.data.columns:
            self.data['Annotation'] = pd.NA

        # Create main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

        # Progress label
        self.progress_label = ttk.Label(self.main_frame, text="", font=('Arial', 10))
        self.progress_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Create labels and fields
        self.create_widgets()

        # Load first row
        self.load_row()

    def create_widgets(self):
        # Query ID
        ttk.Label(self.main_frame, text="Query ID:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W,
                                                                                      pady=5)
        self.query_id_label = ttk.Label(self.main_frame, text="", font=('Arial', 10))
        self.query_id_label.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Query
        ttk.Label(self.main_frame, text="Query:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.NW,
                                                                                   pady=5)
        self.query_text = tk.Text(self.main_frame, height=1, width=4, wrap=tk.WORD, font=('Arial', 10))
        self.query_text.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))

        # Query Description
        ttk.Label(self.main_frame, text="Query Description:", font=('Arial', 10, 'bold')).grid(row=3, column=0,
                                                                                               sticky=tk.NW, pady=5)
        self.desc_text = tk.Text(self.main_frame, height=4, width=80, wrap=tk.WORD, font=('Arial', 10))
        self.desc_text.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))

        # Doc ID
        ttk.Label(self.main_frame, text="Document ID:", font=('Arial', 10, 'bold')).grid(row=4, column=0, sticky=tk.W,
                                                                                         pady=5)
        self.doc_id_label = ttk.Label(self.main_frame, text="", font=('Arial', 10))
        self.doc_id_label.grid(row=4, column=1, sticky=tk.W, pady=5)

        # Abstract
        ttk.Label(self.main_frame, text="Abstract:", font=('Arial', 10, 'bold')).grid(row=5, column=0, sticky=tk.NW,
                                                                                      pady=5)
        abstract_frame = ttk.Frame(self.main_frame)
        abstract_frame.grid(row=5, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=(0, 10))

        # Add scrollbar to abstract
        abstract_scrollbar = ttk.Scrollbar(abstract_frame)
        abstract_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.abstract_text = tk.Text(abstract_frame, height=15, width=80, wrap=tk.WORD,
                                     font=('Arial', 10), yscrollcommand=abstract_scrollbar.set)
        self.abstract_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        abstract_scrollbar.config(command=self.abstract_text.yview)

        # Original Label
        ttk.Label(self.main_frame, text="LLM Judgement:", font=('Arial', 10, 'bold')).grid(row=6, column=0, sticky=tk.W,
                                                                                           pady=10)
        self.orig_label_label = ttk.Label(self.main_frame, text="", font=('Arial', 10))
        self.orig_label_label.grid(row=6, column=1, sticky=tk.W, pady=10)

        # Annotation section
        annotation_frame = ttk.LabelFrame(self.main_frame, text="Our Judgement", padding="10")
        annotation_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20, padx=5)
        annotation_frame.columnconfigure(0, weight=1)

        # ADD THIS: Create a frame for the title with checkmark
        title_frame = ttk.Frame(annotation_frame)
        title_frame.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        # Title label
        title_label = ttk.Label(title_frame, text="Annotation", font=('Arial', 10, 'bold'))
        title_label.pack(side=tk.LEFT, padx=(0, 10))

        # Checkmark label (initially empty)
        self.checkmark_label = ttk.Label(title_frame, text="", font=('Arial', 12, 'bold'), foreground='green')
        self.checkmark_label.pack(side=tk.LEFT)

        # Radio buttons for annotation
        self.annotation_var = tk.IntVar(value=-1)

        values = [0, 1, 2, 3, 4]
        descriptions = [
            "0 - Irrelevant",
            "1 - Marginally relevant",
            "2 - Partially relevant",
            "3 - Highly relevant",
            "4 - Perfect match"
        ]

        for i, (val, desc) in enumerate(zip(values, descriptions)):
            rb = ttk.Radiobutton(
                annotation_frame,
                text=desc,
                variable=self.annotation_var,
                value=val
            )
            rb.grid(row=i, column=0, sticky=tk.W, pady=2)
        # Previous annotations for current query
        self.prev_annotations_label = ttk.Label(
            annotation_frame,
            text="Previous judgement for this query: None",
            font=('Arial', 10)
        )
        self.prev_annotations_label.grid(row=1, column=0, columnspan=5, pady=10)

        # Button frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=8, column=0, columnspan=3, pady=20)

        # Submit button
        self.submit_button = ttk.Button(
            button_frame,
            text="Submit Judgement",
            command=self.submit_annotation,
            width=20
        )
        self.submit_button.pack(side=tk.LEFT, padx=5)

        # Next button
        self.next_button = ttk.Button(
            button_frame,
            text="Next",
            command=self.next_row,
            width=20
        )
        self.next_button.pack(side=tk.LEFT, padx=5)

        # Save button
        self.save_button = ttk.Button(
            button_frame,
            text="Save All",
            command=self.save_all,
            width=20
        )
        self.save_button.pack(side=tk.LEFT, padx=5)

        # Status bar
        self.status_bar = ttk.Label(self.main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

    def load_row(self):
        """Load current row data into widgets"""
        if self.current_index >= self.total_rows:
            messagebox.showinfo("Complete", "All rows have been annotated!")
            return

        row = self.data.iloc[self.current_index]

        # Update progress
        self.progress_label.config(
            text=f"Row {self.current_index + 1} of {self.total_rows} ({(self.current_index + 1) / self.total_rows * 100:.1f}%)"
        )

        # Set widgets with data
        self.query_id_label.config(text=str(row['QueryId']))

        self.query_text.delete(1.0, tk.END)
        self.query_text.insert(1.0, str(row['Query']))
        #         self.query_text.config(state='disabled')

        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(1.0, str(row['QueryDesc']))
        #         self.desc_text.config(state='disabled')

        self.doc_id_label.config(text=str(row['Docid']))

        self.abstract_text.delete(1.0, tk.END)
        self.abstract_text.insert(1.0, str(row['Abstract']))
        #         self.abstract_text.config(state='disabled')

        self.orig_label_label.config(text=str(row['Label']))

        # Set annotation if exists
        #         if pd.notna(row['Annotation']):
        #             self.annotation_var.set(int(row['Annotation']))
        #         else:
        #             self.annotation_var.set(-1)

        if pd.notna(row['Annotation']):
            annotation_value = int(row['Annotation'])
            self.annotation_var.set(annotation_value)
            # ADD THIS: Show green checkmark and update label
            self.checkmark_label.config(text="✓")
            # Optional: Also update the existing annotation label if you have it
            if hasattr(self, 'existing_annotation_label'):
                self.existing_annotation_label.config(text=f"Existing: {annotation_value}")
            self.checkmark_label.config(text="✓")
        else:
            self.annotation_var.set(-1)
            # ADD THIS: Hide checkmark
            self.checkmark_label.config(text="")
            if hasattr(self, 'existing_annotation_label'):
                self.existing_annotation_label.config(text="Existing: NA")
            self.checkmark_label.config(text="")

        # Update status
        self.status_bar.config(text=f"Loaded row {self.current_index + 1}")
        if pd.notna(row['Annotation']):
            prev_annotation = int(row['Annotation'])
            self.prev_annotations_label.config(
                text=f"Previous judgement for this document: {prev_annotation}",
                foreground='green'
            )
        else:
            self.prev_annotations_label.config(
                text="Previous judgement for this document: None",
                foreground='black'
            )

    def submit_annotation(self):
        """Save annotation for current row"""
        if self.annotation_var.get() == -1:
            messagebox.showwarning("Warning", "Please select an annotation value before submitting.")
            return

        # Save annotation
        self.data.at[self.current_index, 'Annotation'] = self.annotation_var.get()

        # Enable next button
        self.next_button.config(state='normal')

        # Update status
        self.status_bar.config(text=f"Annotation {self.annotation_var.get()} saved for row {self.current_index + 1}")

        # Move to next row automatically
        self.next_row()

    def next_row(self):
        """Load next row"""
        # Save current state if annotation exists
        if self.annotation_var.get() != -1:
            self.data.at[self.current_index, 'Annotation'] = self.annotation_var.get()

        # Move to next row
        self.current_index += 1

        if self.current_index < self.total_rows:
            # Reset annotation selection
            self.annotation_var.set(-1)
            # Load next row
            self.load_row()
        else:
            messagebox.showinfo("Complete", "All rows have been annotated!")
            self.status_bar.config(text="All rows annotated - please save your work")

    def save_all(self):
        """Save all annotations back to TSV file"""
        try:
            # Create backup if file exists
            #            if os.path.exists(self.tsv_file):
            #                backup_file = self.tsv_file.replace('.tsv', '_backup.tsv')
            #                self.data.to_csv(backup_file, sep='\t', index=False, header=False)

            # Save with annotations as 7th column
            self.data.to_csv(self.tsv_file, sep='\t', index=False, header=False)

            # Count annotations
            annotated = self.data['Annotation'].count()
            messagebox.showinfo("Saved",
                                f"Annotations saved successfully!\n"
                                f"Annotated rows: {annotated}/{self.total_rows}")
            self.status_bar.config(text=f"Saved! Annotated: {annotated}/{self.total_rows}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def on_closing(self):
        """Handle window closing"""
        if messagebox.askyesno("Quit", "Do you want to save before quitting?"):
            self.save_all()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotation_file', default='./test_annot_UI.tsv')
    args = parser.parse_args()

    # Get TSV file path
    tsv_file = args.annotation_file
    if not os.path.exists(tsv_file):
        print(f"Error: TSV file '{tsv_file}' not found!")
        print("Please ensure the TSV file is in the same directory as this script.")
        return

    # Create GUI
    root = tk.Tk()
    app = TSVAnnotator(root, tsv_file)

    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Start main loop
    root.mainloop()


if __name__ == "__main__":
    main()
