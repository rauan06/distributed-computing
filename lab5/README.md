# Lab 5: Mini-MapReduce on Amazon EMR

This repository contains the implementation of a Word Count MapReduce job for Lab 5 of the Distributed Computing course.

## Repository Structure

```
.
├── mapper.py           # Mapper script (emits word, 1 pairs)
├── reducer.py          # Reducer script (aggregates word counts)
├── test_local.sh       # Script to test MapReduce locally
├── README.md           # This file
└── report.tex          # LaTeX report (compile separately)
```

## Prerequisites

- AWS Account with EMR access (AWS Academy Learner Lab)
- SSH key pair (vockey) configured
- Basic knowledge of Hadoop and MapReduce

## Dataset

We use the Simple English Wikipedia corpus from:
https://github.com/LGDoor/Dump-of-Simple-EnglishWiki

## Local Testing (Optional)

Before deploying to EMR, you can test the MapReduce job locally:

```bash
# Make scripts executable
chmod +x mapper.py reducer.py test_local.sh

# Run local test
./test_local.sh
```

This will simulate the MapReduce pipeline on a small sample dataset.

## EMR Cluster Setup

### Step 1: Launch EMR Cluster

1. Start AWS Academy Learner Lab
2. Navigate to EMR service in AWS Console
3. Click "Create cluster"
4. Configure cluster:
   - **Name**: lab5-mapreduce-cluster
   - **Cluster configuration**: Instance groups
   - **Primary node**: m4.large (1 instance)
   - **Core nodes**: m4.large (start with 1-2 instances)
   - **Task nodes**: m4.large (optional, for scaling experiments)
   - **Security**: EC2 key pair = vockey
   - **IAM roles**:
     - EMR service role: EMR_DefaultRole
     - EC2 instance profile: EMR_EC2_DefaultRole
   - **Applications**: Hadoop (required), Hive (optional)
   - **Cluster logs**: Uncheck "Publish cluster-specific logs to S3" if you encounter bucket issues

5. Click "Create cluster" and wait for status to become "Waiting"

### Step 2: Connect to Master Node

```bash
# Get the Master public DNS from EMR console
# Replace <master-public-dns> with actual DNS
ssh -i vockey.pem hadoop@<master-public-dns>
```

### Step 3: Verify Cluster

```bash
# Check YARN nodes
yarn node -list

# Check HDFS status
hdfs dfsadmin -report

# Create necessary HDFS directories
hdfs dfs -mkdir -p /user/hadoop/input
hdfs dfs -mkdir -p /user/hadoop/output
```

## Dataset Preparation

On the EMR master node:

```bash
# Download the dataset
wget https://github.com/LGDoor/Dump-of-Simple-EnglishWiki/raw/refs/heads/master/corpus.tgz

# Verify and extract
ls -lh corpus.tgz
tar -xvzf corpus.tgz

# Upload to HDFS
hdfs dfs -put corpus.txt /user/hadoop/input/

# Verify upload
hdfs dfs -ls /user/hadoop/input/
hdfs dfs -du -h /user/hadoop/input/
```

## Running the MapReduce Job

### Step 1: Upload Scripts to EMR

From your local machine, copy the Python scripts to EMR:

```bash
scp -i vockey.pem mapper.py reducer.py hadoop@<master-public-dns>:~
```

### Step 2: Make Scripts Executable

On the EMR master node:

```bash
chmod +x mapper.py reducer.py
```

### Step 3: Run the Hadoop Streaming Job

```bash
# Remove output directory if it exists from previous runs
hdfs dfs -rm -r /user/hadoop/output

# Run the MapReduce job
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming.jar \
  -input /user/hadoop/input/ \
  -output /user/hadoop/output/ \
  -mapper mapper.py \
  -reducer reducer.py \
  -files mapper.py,reducer.py
```

The job will display progress information. Wait for completion.

### Step 4: Verify Output

```bash
# List output files
hdfs dfs -ls /user/hadoop/output/

# View top results
hdfs dfs -cat /user/hadoop/output/part-00000 | head -20

# Count total unique words
hdfs dfs -cat /user/hadoop/output/part-* | wc -l

# Get output to local file (optional)
hdfs dfs -get /user/hadoop/output/part-00000 wordcount_results.txt
```

## Experimentation

### Scenario A: Scaling (Varying Core Nodes)

1. **Baseline (2 core nodes)**:
   ```bash
   # Note the job completion time from Hadoop output
   ```

2. **Scale up (4 core nodes)**:
   - Modify EMR cluster to add more core nodes
   - Re-run the job with same dataset
   - Compare execution time

3. **Observations**:
   - Record job duration for each configuration
   - Note the difference in parallel processing
   - Document in report

### Scenario B: Input Size Variation

1. **Small dataset**:
   ```bash
   # Use only part of corpus
   hdfs dfs -put corpus_small.txt /user/hadoop/input/
   ```

2. **Large dataset**:
   ```bash
   # Use full corpus or multiple files
   hdfs dfs -put corpus.txt /user/hadoop/input/
   ```

3. Compare execution times and resource utilization

### Scenario C: Fault Tolerance (Advanced)

1. Start a MapReduce job
2. During execution, terminate one worker node from AWS Console
3. Observe YARN's recovery behavior
4. Check if job completes successfully
5. Document findings

## Monitoring

- **YARN Resource Manager UI**: http://<master-public-dns>:8088
- **HDFS NameNode UI**: http://<master-public-dns>:9870
- **Job History**: View completed jobs in YARN UI

## Troubleshooting

### Common Issues

1. **Permission denied for scripts**:
   ```bash
   chmod +x mapper.py reducer.py
   ```

2. **Output directory already exists**:
   ```bash
   hdfs dfs -rm -r /user/hadoop/output
   ```

3. **Python not found**:
   - Ensure scripts use `#!/usr/bin/env python3`
   - Verify Python3 is installed: `python3 --version`

4. **Cluster session expired**:
   - Save results to S3 before session ends
   - Recreate cluster in next session

5. **Instance type not supported**:
   - Use only: nano, micro, small, medium, large
   - Recommended: m4.large

## Cleanup

To avoid charges (in non-Academy environments):

```bash
# Remove HDFS data
hdfs dfs -rm -r /user/hadoop/input
hdfs dfs -rm -r /user/hadoop/output

# Terminate EMR cluster from AWS Console
```

## Performance Notes

- **Dataset size**: ~500MB+ recommended for observing parallelism
- **Cluster size**: 2-4 core nodes optimal for this lab
- **Expected runtime**: 2-10 minutes depending on configuration
- **Output**: One file per reducer (part-00000, part-00001, etc.)

## Learning Outcomes

After completing this lab, you should understand:
- MapReduce programming model (Map, Shuffle, Reduce)
- Distributed data processing with Hadoop
- HDFS as distributed storage system
- Parallel execution across cluster nodes
- Job scaling and performance characteristics
- Fault tolerance in distributed systems


## Author

Lab 5 - Distributed Computing Course
Amazon EMR MapReduce Implementation

## License

Academic use only - for course Lab 5 submission