import tkinter as tk
from tkinter import filedialog, messagebox
import cellpose.models as cp_model
import cellpose.resnet_torch as cp_net
import torch
import os

def convert_to_ONNX(model_path: str, output_directory: str, diam_mean: float, batch_size: int = 1):
    model = cp_net.CPnet(
        [2, 32, 64, 128, 256],
        3,
        sz=3,
        mkldnn=None,
        diam_mean=diam_mean)
    
    model.residual_on = True
    model.style_on = True
    model.concatenation = False
    
    model.load_model(model_path)
    model.eval()

    # convert to onnx
    onnx_model_path = os.path.join(output_directory, os.path.split(model_path)[-1] + ".onnx")
    dummy = torch.randn(batch_size, 2, 224, 224, requires_grad=True)
    torch.onnx.export(
        model,
        dummy,
        onnx_model_path,
        verbose=False,
        export_params=True,
        opset_version=12,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output', 'style'])

def convert_all_models(output_directory: str):
    all_models = cp_model.MODEL_NAMES.copy()
    model_strings = cp_model.get_user_models()
    all_models.extend(model_strings)

    for model_type in all_models:
        model_string = model_type if model_type is not None else 'cyto'
        if model_string == 'nuclei':
            diam_mean = 17.
        else:
            diam_mean = 30.

        if model_type in ['cyto', 'cyto2', 'cyto3', 'nuclei']:
            model_range = range(4)
        else:
            model_range = range(1)

        model_paths = [cp_model.model_path(model_string, j, True) for j in model_range]

        for model_path in model_paths:
            convert_to_ONNX(model_path, output_directory, diam_mean)

def start_conversion(model_path, output_directory, mean_diameter):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    if model_path:
        if mean_diameter not in [17.0, 30.0]:
            messagebox.showerror("Error", "Mean diameter must be either 17.0 (for nuclei-based models) or 30.0 for all other models.")
            return
        convert_to_ONNX(model_path=model_path, output_directory=output_directory, diam_mean=mean_diameter)
    else:
        convert_all_models(output_directory)
    
    messagebox.showinfo("Info", f"Output models are saved here: {output_directory}\nConversion completed.")

def select_model_path(entry):
    model_path = filedialog.askopenfilename()
    entry.delete(0, tk.END)
    entry.insert(0, model_path)

def select_output_directory(entry):
    output_directory = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(0, output_directory)

def create_gui():
    root = tk.Tk()
    root.title("Cellpose to ONNX Converter")
    root.configure(bg='black')

    tk.Label(root, text="Model Path:", fg='white', bg='black').grid(row=0, column=0, padx=10, pady=5)
    model_path_entry = tk.Entry(root, width=50)
    model_path_entry.grid(row=0, column=1, padx=10, pady=5)
    tk.Button(root, text="Browse", command=lambda: select_model_path(model_path_entry)).grid(row=0, column=2, padx=10, pady=5)

    tk.Label(root, text="Output Directory:", fg='white', bg='black').grid(row=1, column=0, padx=10, pady=5)
    output_directory_entry = tk.Entry(root, width=50)
    output_directory_entry.grid(row=1, column=1, padx=10, pady=5)
    tk.Button(root, text="Browse", command=lambda: select_output_directory(output_directory_entry)).grid(row=1, column=2, padx=10, pady=5)

    tk.Label(root, text="Mean Diameter:", fg='white', bg='black').grid(row=2, column=0, padx=10, pady=5)
    mean_diameter_entry = tk.Entry(root, width=50)
    mean_diameter_entry.grid(row=2, column=1, padx=10, pady=5)

    tk.Button(root, text="Convert", command=lambda: start_conversion(
        model_path_entry.get(), output_directory_entry.get(), float(mean_diameter_entry.get()))).grid(row=3, column=1, padx=10, pady=20)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
