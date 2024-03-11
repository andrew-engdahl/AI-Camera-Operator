## Prerequisites 

# Install Mediapip
```
pip install -q mediapipe
```
#Install Mido with the default backend
```
pip install mido[ports-rtmidi]
```
Then download an off-the-shelf model bundle. Check out the MediaPipe documentation for more information about this model bundle.

```
wget -O pose_landmarker.task -q https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task
```
