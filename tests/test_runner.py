# Built-in Imports
import time
import unittest
import pathlib
import shutil
import os
import sys

# Third-Party Imports
import pandas as pd
import tqdm

# PyMMDT Library
import pymmdt as mm
import pymmdt.tabular as mmt
import pymmdt.video as mmv

# Testing package
from . import test_doubles

# Constants
CURRENT_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = CURRENT_DIR.parent
RAW_DATA_DIR = CURRENT_DIR / 'data' 
OUTPUT_DIR = CURRENT_DIR / 'test_output' 

sys.path.append(str(ROOT_DIR))

class SingleRunnerTestCase(unittest.TestCase):

    def setUp(self):

        # Storing the data
        self.csv_data = pd.read_csv(RAW_DATA_DIR/"example_use_case"/"test.csv")
        self.csv_data['_time_'] = pd.to_timedelta(self.csv_data['time'], unit="s")

        # Create each type of data stream
        self.tabular_ds = mmt.TabularDataStream(
            name="test_tabular",
            data=self.csv_data,
            time_column="_time_"
        )
        self.video_ds = mmv.VideoDataStream(
            name="test_video",
            start_time=pd.Timedelta(0),
            video_path=RAW_DATA_DIR/"example_use_case"/"test_video1.mp4",
            fps=30
        )
        
        # Clear out the previous pymmdt run 
        # since pipeline is still underdevelopment
        exp_dir = OUTPUT_DIR / "pymmdt"
        if exp_dir.exists():
            shutil.rmtree(exp_dir)

        # Construct the individual participant pipeline object
        # Create an overall session and pipeline
        self.session = mm.Session(
            log_dir = OUTPUT_DIR,
            experiment_name = "pymmdt"
        )

        # Use a test pipeline
        individual_pipeline = test_doubles.TestPipe()

        # Load construct the first runner
        self.runner = mm.SingleRunner(
            name='P01',
            data_streams=[self.tabular_ds, self.video_ds],
            pipe=individual_pipeline,
            session=self.session,
            time_window_size=pd.Timedelta(seconds=3),
            run_solo=True,
            verbose=True
        )

    def test_single_runner_and_collector_together(self):

        # Start 
        self.runner.start()

        # And start the threads
        self.runner.loading_thread.start()
        self.runner.processing_thread.start()

        # Creating a loading bar to show the step of processing data
        pbar = tqdm.tqdm(total=len(self.runner.collector.windows), desc="Processing data")
        last_value = 0

        # Update the loading bar is it continues
        while True:
            if last_value != self.runner.num_processed_data_chunks:
                diff = self.runner.num_processed_data_chunks - last_value
                last_value = self.runner.num_processed_data_chunks
                pbar.update(diff)

            if last_value == len(self.runner.collector.windows):
                break

        # And wait until the threads stop
        self.runner.processing_thread.join()
        self.runner.loading_thread.join()

    def test_single_runner_and_session_together(self):
        
        # Start 
        self.runner.start()
        
        # And start the threads
        self.runner.processing_thread.start()
        for thread in self.runner.logging_threads:
            thread.start()

        sample_data = {
            self.runner.name: {
                'test': pd.DataFrame({'a':[1], 'b': [1]})
            }
        }
        end_sample_data = {
            'END'
        }

        self.runner.logging_queues[0].put(sample_data)
        self.runner.logging_queues[0].put(end_sample_data)
        
        # And wait until the threads stop
        self.runner.processing_thread.join()
        for thread in self.runner.logging_threads:
            thread.join()

        # Check the session indeed save the data
        entry = self.session.records['test']
        assert entry.file.exists()

    def test_single_runner_collector_and_session_together(self):
        ...

    def test_single_runner_run(self):
        ...

class GroupRunnerTestCase(unittest.TestCase):

    def setUp(self):

        # Load the data for all participants (ps)
        nursing_session_dir = RAW_DATA_DIR / 'nurse_use_case'
        ps = pymmdt.utils.tobii.load_session_data(nursing_session_dir, verbose=True)

        # Clear out the previous pymmdt run 
        # since pipeline is still underdevelopment
        exp_dir = OUTPUT_DIR / "pymmdt"
        if exp_dir.exists():
            shutil.rmtree(exp_dir)

        # Then for each participant, we need to setup their own session,
        # pipeline, and runner
        self.runners = []
        for p_id, p_elements in ps.items():
            
            # Construct the individual participant pipeline object
            individual_pipeline = mm.Pipe()

            runner = mm.SingleRunner(
                name=p_id,
                data_streams=p_elements['data'],
                pipe=individual_pipeline,
            )

            # Store the individual's runner to a list 
            self.runners.append(runner)
        
        # Create an overall session and pipeline
        total_session = mm.Session(
            log_dir = OUTPUT_DIR,
            experiment_name = "pymmdt"
        )
        overall_pipeline = mm.Pipe()

        # Pass all the runners to the Director
        self.director = mm.GroupRunner(
            name="Nurse Teamwork Example #1",
            pipe=overall_pipeline,
            runners=self.runners, 
            session=total_session,
            time_window_size=pd.Timedelta(seconds=5),
            verbose=True
        )

    def test_group_runner_run(self):

        # Run the director
        self.director.run()

if __name__ == "__main__":
    # Run when debugging is not needed
    # unittest.main()

    # Otherwise, we have to call the test ourselves
    # test_case = GroupNurseTestCase()
    single_test_case = SingleRunnerTestCase()
    single_test_case.setUp()
    single_test_case.test_runner_get_data_and_step_process()