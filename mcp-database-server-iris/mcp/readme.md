## Running the Example

The project includes an example client in `example/example.py`. To run it:

1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   pip install -e ..
   ```

2. Configure your environment:
   Edit `.env` file with your InterSystems IRIS settings:
   ```env
   IRIS_HOSTNAME=localhost
   IRIS_PORT=1972
   IRIS_NAMESPACE=USER
   IRIS_USERNAME=_SYSTEM
   IRIS_PASSWORD=SYS
   ```

3. Run the example:
   ```bash
   python example.py
   ```
