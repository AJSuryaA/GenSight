import os
import shutil
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import RedirectResponse
from fastapi import BackgroundTasks
import uuid
import json
from typing import Dict
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


from app.backend.workflows.data_info.pandas_processing import get_dataset_info as get_pandas_info
from app.backend.workflows.data_info.pyspark_processing import get_dataset_info as get_pyspark_info

from app.backend.workflows.eda.pandas_eda import pandas_eda
from app.backend.workflows.eda.pyspark_eda import pyspark_eda
import pandas as pd
from pyspark.sql import SparkSession

from app.backend.workflows.eda.pandas_profiling_eda import generate_pandas_eda_report

from app.backend.workflows.eda.gpt_integration import create_eda_summary_prompt, call_gpt_api, parse_gpt_structured_response, create_eda_summary_prompt_spark
from app.backend.workflows.eda.data_cleaning_pyspark import clean_data_spark, save_cleaned_spark, drop_columns_spark, drop_empty_columns_spark 

from app.backend.workflows.eda.data_cleaning_pandas import clean_data, save_cleaned_data

from app.backend.workflows.model_training.pandas_ml_training import train_models_pandas 
from app.backend.workflows.model_training.pyspark_ml_training import *

from app.backend.workflows.data_visualization.visualization import plot_from_gpt_dict
from app.backend.workflows.data_visualization.gpt_visualization import (
    create_visuvalization_summary_prompt,
    call_gpt_api,
    parse_gpt_visualization_response,
)

from app.backend.workflows.data_analysis.gemini_data_analysis import *
from app.backend.workflows.data_analysis import phrase_gemini_response as pgr
from app.backend.workflows.generate_report.generate_report import generate_html

# Global dictionary to track processing tasks (in production, use a proper database)
processing_tasks: Dict[str, dict] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: run before app starts receiving requests

    yield

    # Shutdown: run after app stops receiving requests (optional cleanup)
    # Put any cleanup code here if needed


app = FastAPI(lifespan=lifespan)

# Paths for frontend files (adjust if needed)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

templates = Jinja2Templates(directory="templates")

# Directory to save uploaded files temporarily before moving to data lake
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/reports", StaticFiles(directory="app/backend/workflows/eda/reports"), name="reports")
app.mount("/logs", StaticFiles(directory="logs"), name="logs")
app.mount("/eda_report", StaticFiles(directory="eda_report"), name="eda_report")

LOG_FILE = "logs/mylog.jsonl"
report_file= "eda_report/report.html"

thread = None
with open(LOG_FILE, "w") as f:
    f.write("")  # Clear file
    
import os

folder = "plots"
for filename in os.listdir(folder):
    file_path = os.path.join(folder, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)


# Serve the upload page
@app.get("/")
async def read_index():
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))

@app.get("/workflow_monitor")
async def read_workflow_monitor():
    return FileResponse(os.path.join(TEMPLATES_DIR, "workflow_monitor.html"))

@app.post("/eda_report")
async def serve_report():
    try:
        return RedirectResponse(url=report_file, status_code=303)
    except Exception as e:
        return HTMLResponse(content=f"Error loading report: {str(e)}", status_code=500)


    
def check_hadoop_running():
    try:
        result = subprocess.run(['jps'], capture_output=True, text=True)
        running_services = [line.split()[1] for line in result.stdout.strip().split('\n') if len(line.split()) > 1]

        required_services = ['NameNode', 'DataNode', 'ResourceManager', 'NodeManager']
        missing_services = [service for service in required_services if service not in running_services]

        if missing_services:
            print(f"Missing Hadoop services: {missing_services}")
            return False
        print("All essential Hadoop services are running.")
        return True
    except Exception as e:
        print(f"Error checking Hadoop services: {e}")
        return False


def start_hadoop_services():
    try:
        # Replace with your actual Hadoop sbin path
        hadoop_home = os.environ.get('HADOOP_HOME')
        hadoop_sbin_path = f'{hadoop_home}/sbin'
        subprocess.run(['bash', f'{hadoop_sbin_path}/start-dfs.sh'], check=True)
        subprocess.run(['bash', f'{hadoop_sbin_path}/start-yarn.sh'], check=True)
        print("Hadoop DFS and YARN started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start Hadoop services: {e}")


def ensure_hadoop_running():
    if not check_hadoop_running():
        print("Hadoop services not running. Starting services...")
        start_hadoop_services()
        create_log(process= "Checking Hadoop services :", response= f"Hadoop services not running. Starting services...", print_effect="print entirely")
    
    else:
        print("Hadoop services already running.")

        create_log(process= "Checking Hadoop services :", response= f"Hadoop services already running.", print_effect="print entirely")
    

def create_log(process: str, response, print_effect= "type effect", final= "Process : Task completed successfully!"):
    process_log = {
            f"{process}": [
                f"Process : Starting task...",
                "print entirely",
                f"{response}",
                f"{print_effect}",
                f"{final}",
                "print entirely"
            ]
        }
    
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(process_log) + "\n")


def choose_processing_mode(file_path, command_input=None):
    SIZE_THRESHOLD = 100 * 1024 * 1024  # 100MB
    if command_input:
        if command_input.strip() == "-f:p":
            return "pandas"
        elif command_input.strip() == "-f:ps":
            return "pyspark"

    file_size = os.path.getsize(file_path)
    if file_size <= SIZE_THRESHOLD:
        return "pandas"
    else:
        return "pyspark"

def upload_to_hdfs(local_file_path, hdfs_dir="/user/gen_sight/uploads"):
    try:
        subprocess.run(["hdfs", "dfs", "-mkdir", "-p", hdfs_dir], check=True)
        result = subprocess.run(
            ["hdfs", "dfs", "-put", "-f", local_file_path, hdfs_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return os.path.join(hdfs_dir, os.path.basename(local_file_path))
    except subprocess.CalledProcessError as e:
        print(f"Error uploading to HDFS: {e.stderr}")
        raise

def normalize_structured_data(data_dict):
    for key in ['problem_type', 'target_column', 'label_encoding', 'drop_columns', 'standard_scalar']:
        val = data_dict.get(key)
        if isinstance(val, list):
            if len(val) == 1:
                data_dict[key] = val[0]  # convert single-entry lists to plain string
            else:
                data_dict[key] = val  # keep lists as-is if multiple elements
    return data_dict

def visualize_from_gpt_result(data: pd.DataFrame, gpt_result: dict, target_col="target", y_true=None, y_pred=None, y_score=None, save_dir="plots"):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    plot_from_gpt_dict(data, gpt_result, target_col=target_col, y_true=y_true, y_pred=y_pred, y_score=y_score)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), command: str = Form(None)):
    try:
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Save the file temporarily
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        await file.close()

        # Determine processing mode
        mode = choose_processing_mode(file_location, command)
        
        # user file upload
        create_log(process= "1", response= "0", print_effect="none", final="blinkNode")
        create_log(process= "1", response= "0", print_effect="none", final="highlightNodeGreen")
        create_log(process= "User File upload", response= "file upload started . . . .")
        
        # pandas / pyspark
        create_log(process= "1", response= "2", print_effect="none", final="setConnectionYellowGlow")
        create_log(process= "2", response= "0", print_effect="none", final="blinkNode")
        create_log(process= "Choosing Processing Mode :", response= f"Mode: {mode}", print_effect="print entirely")        
        create_log(process= "1", response= "2", print_effect="none", final="setConnectionGreen" )
        create_log(process= "2", response= "0", print_effect="none", final="highlightNodeGreen")
        create_log(process= "2", response= "panel-left", print_effect="none", final="setConnectionYellowGlow")
        create_log(process= "3", response= "0", print_effect="none", final="blinkNode")

        # Store task information
        processing_tasks[task_id] = {
            "status": "uploaded",
            "file_location": file_location,
            "mode": mode,
            "command": command,
            "result": None,
            "error": None
        }

        # Return success with redirect and task ID
        return JSONResponse({
            "status": "upload_success",
            "task_id": task_id,
            "redirect_url": f"/workflow_monitor?task_id={task_id}"
        })
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.post("/start_processing/{task_id}")
async def start_processing(task_id: str, background_tasks: BackgroundTasks):
    if task_id not in processing_tasks:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    
    task = processing_tasks[task_id]
    if task["status"] != "uploaded":
        return JSONResponse(status_code=400, content={"error": "Task already processed"})
    
    # Start processing in background
    task["status"] = "processing"
    background_tasks.add_task(process_uploaded_file, task_id)
    
    return JSONResponse({"status": "processing_started"})

@app.get("/processing_status/{task_id}")
async def get_processing_status(task_id: str):
    if task_id not in processing_tasks:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    
    return JSONResponse(processing_tasks[task_id])

async def process_uploaded_file(task_id: str):
    try:
        task = processing_tasks[task_id]
        file_location = task["file_location"]
        mode = task["mode"]
        
        if mode == "pandas":
            
            # file upload success  

            create_log(process= "file upload", response= f"file uploaded sucessfully\nlocation: {file_location}")
            create_log(process= "2", response= "panel-left", print_effect="none", final="setConnectionGreen" )
            create_log(process= "3", response= "0", print_effect="none", final="highlightNodeGreen")

            
            dataset_info = get_pandas_info(file_location)
            create_log(process= "Getting Data info ....", response= f"{dataset_info}")

            
            # Run EDA for pandas
            df = pd.read_csv(file_location)

            report_file = generate_pandas_eda_report(df)
            report_url = report_file.replace("app/backend", "app/backend/workflows/eda/reports")
            create_log(process= "generating basic EDA ....", response= f"file location :{report_url}")

            # Create EDA prompt
            create_log(process= "3", response= "4", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "4", response= "0", print_effect="none", final="blinkNode")
            eda= pandas_eda(df)
            create_log(process= "Advanced EDA", response= f"eda result :{eda}")
            create_log(process= "3", response= "4", print_effect="none", final="setConnectionGreen" )
            create_log(process= "4", response= "0", print_effect="none", final="highlightNodeGreen")

            
            create_log(process= "panel-left", response= "panel-ai1", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "9", response= "0", print_effect="none", final="blinkNode")
            # creating prompt
            prompt = create_eda_summary_prompt(df)
            create_log(process= "Creating prompt:", response= f"{prompt}")  
            # Call GPT API
            gpt_response = call_gpt_api(prompt)
            create_log(process= "Prompting Sonar-Pro AI :", response= f"Sonar-Pro Response:\n{gpt_response}")            
            create_log(process= "panel-left", response= "panel-ai1", print_effect="none", final="setConnectionGreen" )
            create_log(process= "9", response= "0", print_effect="none", final="highlightNodeGreen")
                        

            create_log(process= "9", response= "10", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "10", response= "0", print_effect="none", final="blinkNode")
            # Parse GPT response to get columns to drop
            structured_data = parse_gpt_structured_response(gpt_response)
            create_log(process= "Parsing Sonar-Pro Response :", response= f"Parsed Output:\n{structured_data}")
            create_log(process= "9", response= "10", print_effect="none", final="setConnectionGreen" )
            create_log(process= "10", response= "0", print_effect="none", final="highlightNodeGreen")
                        

            create_log(process= "panel-ai1", response= "11", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "11", response= "0", print_effect="none", final="blinkNode")
            df_cleaned = clean_data(df, structured_data)
            create_log(process= "Data Cleaning :", response= "Data cleaning with Ai recommendation ")
            create_log(process= "panel-ai1", response= "11", print_effect="none", final="setConnectionGreen" )
            create_log(process= "11", response= "0", print_effect="none", final="highlightNodeGreen")


            create_log(process= "11", response= "12", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "12", response= "0", print_effect="none", final="blinkNode")
            save_cleaned_data(df_cleaned, "data.csv")
            create_log(process= "Saving Cleaned data :", response= "the data is cleaned and stored sucessfully")
            create_log(process= "11", response= "12", print_effect="none", final="setConnectionGreen" )
            create_log(process= "12", response= "0", print_effect="none", final="highlightNodeGreen")
            
           
            print("sonar raw response:", gpt_response)           
            print("Parsed GPT Data:", structured_data)
            
            
            # model Training
            best_models = train_models_pandas(df, structured_data)
            create_log(process= "Training Model :", response= f"Machine learing model trained\nbest models :{best_models}")

            
            for model_name, result in best_models.items():
                print(f"Model: {model_name}")
                if 'best_params' in result:
                    print("Best Parameters:", result['best_params'])
                    print("Best CV Score:", result['best_score'])
                    print("Test Score:", result['test_score'])
                else:
                    print("Test Score:", result['score'])
                print("-" * 40)

            # Example file path - update with your actual data file
            file_location = "/home/master_node/GenSight/uploaded_files/data.csv"

            # Load the cleaned dataframe
            df = pd.read_csv(file_location)
            
            problem_type = structured_data.get('problem_type', [None])[0]
            print("problem Type : ", problem_type)
            

            create_log(process= "12", response= "panel-ai2", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "15", response= "0", print_effect="none", final="blinkNode")
            # Create prompt to send to GPT
            prompt = create_visuvalization_summary_prompt(df,  problem_type)
            print("Prompt sent to GPT:\n", prompt)
            create_log(process= "Creating Prompt(visualization) :", response= f"prompt:\n{prompt}")
            # Call GPT API (uncomment below when API key is set)
            response_text = call_gpt_api(prompt)
            print("\nRaw GPT response:\n", response_text)
            create_log(process= "Prompting Gemini Ai for visualization recommendation :", response= f"Gemini Response:\n{response_text}")
            create_log(process= "12", response= "panel-ai2", print_effect="none", final="setConnectionGreen" )
            create_log(process= "15", response= "0", print_effect="none", final="highlightNodeGreen")
            

            create_log(process= "15", response= "16", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "16", response= "0", print_effect="none", final="blinkNode")
            # Parse the GPT response into a dictionary
            parsed_result = parse_gpt_visualization_response(response_text)
            print("\nParsed visualization dictionaries:\n", parsed_result) 
            create_log(process= "Parsing Gemini Ai Response :", response= f"Parsed Gemini Response:\n{parsed_result}")           
            create_log(process= "15", response= "16", print_effect="none", final="setConnectionGreen" )
            create_log(process= "16", response= "0", print_effect="none", final="highlightNodeGreen")


            # For testing without API call, you can assign response_text manually, e.g.:
            # response_text = """result = { ... }"""
            # Example: if you have true labels and predictions from model (required for confusion matrix/ROC)
            # Replace these with your actual values after model prediction
            y_true = df['target'] if 'target' in df.columns else None
            y_pred = None  # provide your predictions here, e.g., model.predict(X_test)
            y_score = None  # provide predicted probabilities/scores here if available


            create_log(process= "panel-ai2", response= "17", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "17", response= "0", print_effect="none", final="blinkNode") 
            # Generate visualizations based on GPT instructions
            visualize_from_gpt_result(df, parsed_result, target_col='target', y_true=y_true, y_pred=y_pred, y_score=y_score)
            # Folder with generated visualization images
            folder_path = "/home/master_node/GenSight/plots"
            create_log(process= "Generating Visualization recommended by Ai", response= f"Visualization started and the plots will be saved at : {folder_path} ")
            create_log(process= "panel-ai2", response= "17", print_effect="none", final="setConnectionGreen" )
            create_log(process= "17", response= "0", print_effect="none", final="highlightNodeGreen")


            
            # Load your dataframe (update path)
            df = pd.read_csv("/home/master_node/GenSight/uploaded_files/data.csv")

            create_log(process= "17", response= "18", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "18", response= "0", print_effect="none", final="blinkNode")
            create_log(process= "Saving Visualization grnerated", response= f"Visualization images saved at : {folder_path} ")
            create_log(process= "17", response= "18", print_effect="none", final="setConnectionGreen" )
            create_log(process= "18", response= "0", print_effect="none", final="highlightNodeGreen")


            create_log(process= "18", response= "panel-ai3", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "19", response= "0", print_effect="none", final="blinkNode")
            df_summary = generate_dataframe_summary(df)
            images = read_images_from_folder(folder_path)
            print(df_summary)
            create_log(process= "Creating Prompt for plots insight", response= f"prompt : {df_summary} ")
            create_log(process= "17", response= "18", print_effect="none", final="setConnectionGreen" )
            create_log(process= "18", response= "panel-ai3", print_effect="none", final="setConnectionGreen" )
            create_log(process= "19", response= "0", print_effect="none", final="highlightNodeGreen")
            
            client = Client(api_key=os.getenv("Gemini_API"))  # Make sure GOOGLE_APPLICATION_CREDENTIALS is set for authentication


            create_log(process= "19", response= "20", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "20", response= "0", print_effect="none", final="blinkNode")

            analysis = analyze_with_gemini(client, df_summary, images)
            print("\nGemini API Analysis Result:\n", analysis)
            eda_summary_str, image_insights_list, summary_str = pgr.extract_sections_from_gpt_response(analysis)
            # Print/results example:
            print("EDA Summary:\n", eda_summary_str)
            print("\nImage Insights:")
            for img, insight in image_insights_list:
                print(f"{img}: {insight}")
            print("\nSummary Insights:\n", summary_str)
            create_log(process= "Parsing Gemini Ai for image insights", response= f"Gemini Response : {eda_summary_str, image_insights_list}\n{image_insights_list}\n{summary_str} ")
            create_log(process= "19", response= "20", print_effect="none", final="setConnectionGreen" )
            create_log(process= "20", response= "0", print_effect="none", final="highlightNodeGreen")


            create_log(process= "panel-ai3", response= "21", print_effect="none", final="setConnectionYellowGlow")
            create_log(process= "21", response= "0", print_effect="none", final="blinkNode")
            print("Generating GenSight report...")
            generate_html(eda_summary_str, image_insights_list, summary_str)
            create_log(process= "Generating HTML :", response= f"Gemini Response is parsed and converted into HTML for user")
            create_log(process= "panel-ai3", response= "21", print_effect="none", final="setConnectionGreen" )
            create_log(process= "21", response= "0", print_effect="none", final="highlightNodeGreen")
            
            #program end
            create_log(process= "", response= "", print_effect="final", final="highlightNodeGreen")


            task["result"] = {"message": "Pandas processing completed"}

            return JSONResponse({
                # other fields...
                # "eda_report_url": report_url,
                "original_columns": list(df.columns),
                # "columns_removed": cols_to_drop,
                # "cleaned_file_path": cleaned_path,
                "gpt_suggestions": gpt_response
            })
            
            
        elif mode == "pyspark":
            ensure_hadoop_running()
                           
            hdfs_path = upload_to_hdfs(file_location)
            dataset_info = get_pyspark_info(hdfs_path)
            spark = SparkSession.builder \
                .appName("PySparkModelTraining") \
                .config("spark.driver.bindAddress", "127.0.0.1") \
                .config("spark.driver.port", "7077") \
                .getOrCreate()
            
            print("✅ Spark session started")

            try:
                print("started_____________________1")
                sdf = spark.read.csv(hdfs_path, header=True, inferSchema=True)
                print("✅ Data loaded. Shape:", (sdf.count(), len(sdf.columns)))
                print("started_____________________2")

                # Drop '_c0' column if exists (common with saved CSVs)
                if '_c0' in sdf.columns:
                    sdf = sdf.drop('_c0')

                print("started_____________________3")
                pyspark_eda(sdf)  # your existing EDA function

                print("started_____________________4")
                prompt = create_eda_summary_prompt_spark(sdf)
                print("pprompt: ", prompt)
                gpt_response = call_gpt_api(prompt)
                
                structured_data = parse_gpt_structured_response(gpt_response)

                print("sonar raw response:", gpt_response)
                print("\n\n" + "\n_______________________________________________________________________")
                print("Parsed GPT Data:", structured_data)
                print("\n\n" + "\n_______________________________________________________________________")

                print("started_____________________5")
                # Clean Spark dataframe based on GPT instructions
                sdf_cleaned = clean_data_spark(sdf, structured_data)
                print("started_____________________6")

                hdfs_exact_file_path = "/user/gen_sight/uploads/data.csv"
                cmd = ["hdfs", "dfs", "-rm", hdfs_exact_file_path]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(result.stdout)

                save_cleaned_spark(sdf_cleaned, hdfs_exact_file_path)
                print("\n\n" + "\n_______________________________________________________________________")

                print("started_____________________7")
                spark_df = spark.read.csv(hdfs_exact_file_path, header=True, inferSchema=True)
                print("✅ Data read. Shape:", (spark_df.count(), len(spark_df.columns)))

                best_models = train_models_spark(spark_df, normalize_structured_data(structured_data))

                print("\n\n" + "\n_______________________________________________________________________")
                print("started_____________________8")

                for model_name, info in best_models.items():
                    print(f"Best Model: {model_name}, Metric: {info['metric']}")


                

            except Exception as e:
                spark.stop()
                print(f"Error during PySpark processing: {e}")
                return JSONResponse(status_code=500, content={"error": str(e)})

            spark.stop()


            return JSONResponse({
                # "filename": file.filename,
                "processing_mode": mode,
                "message": "File uploaded and cleaned successfully.",
                "local_path": file_location,
                "hdfs_path": hdfs_path,
                "dataset_info": dataset_info,
                "gpt_suggestions": gpt_response
            })
        
        task["status"] = "completed"
        
    except Exception as e:
        task["status"] = "error"
        task["error"] = str(e)
        print(f"Error processing task {task_id}: {e}")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


        

        # Upload to HDFS
        # print(f"Uploading file to HDFS: {file_location} => directory: /user/gen_sight/uploads")
        # hdfs_path = upload_to_hdfs(file_location)
        # print(f"File uploaded to HDFS path: {hdfs_path}")


        # Get dataset info based on processing mode