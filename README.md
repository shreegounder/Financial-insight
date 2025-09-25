# EAI 6050 Project

> How to run this project

## Step 1: **Ollama Installation and Model Setup Guide**

### **1. Download and Install Ollama**

Ollama provides a simple way to run **LLMs locally**.

#### **For macOS and Linux**

Open a terminal and run:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### **For Windows**

1. Download the Windows installer from Ollama’s official website.
2. Run the installer and follow the setup instructions.
3. Restart your system if needed.

To verify the installation, run:

```bash
ollama -v
```

### **2. Install DeepSeek-R1:8B**

To install and run the DeepSeek-R1:8B model, run:

```bash
ollama run deepseek-r1:8b
```

run following command to exit deepseek model

```bash
/bye
```

### **4. Verify Models Run**

Run following command to ensure models run properly

```bash
ollama ps
```

## Step 2: **Install Requirements**

Go to project root directory and run the following command

```bash
pip install -r requirements.txt
```

> Note: yahooquery requires python==3.11 to run properly


## Step3: **Run Product**

Go to project root directory and run the following command

```bash
python terminal_run.py
```
