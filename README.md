# DB三人グループ


学籍番号	氏名
2442017　カクヨウカイ  
2441056　陳思竹  
2442049　孫小懿  



# Lost & Found Map App

A Streamlit-based web application for reporting and retrieving lost items on a map.

## Features
- **Interactive Map**: View lost and found items on a map.
- **Submission**: Submit new items with title, description, and location (click on map to set).
- **Search**: Filter items by keywords.
- **Auto-Location**: Clicking an item in the list zooms the map to its location.

## Prerequisites
- Python 3.8+
- PostgreSQL

## Setup & Installation

1.  **Clone the repository** (if applicable)

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Database Configuration**
    Ensure your PostgreSQL server is running locally on port `5432`.
    The app expects the following credentials (configurable in `db.py`):
    - **User**: `guest`
    - **Password**: `password`
    - **Database**: `postgres`

    The table `found_items` will be automatically created on the first run.

## Running the App

Run the Streamlit application:
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

システム構成図
![image](https://github.com/gykkuo/_DB/blob/main/IMG/system.png)


ER図
![image](https://github.com/gykkuo/_DB/blob/main/IMG/ER図.drawio.png)
