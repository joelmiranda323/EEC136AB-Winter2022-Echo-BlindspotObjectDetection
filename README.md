# Blindspot Object Detection
### Our goal
In this repository, my team, Team Echo, developed a final version of our Blindspot 
Object Detection system that uses dual cameras supported by the NVIDIA Jetson Nano 
microcontroller to alerts drivers of objects in their blindspot via LEDs.

### Implementation
blindspot_turnsig.py is our first implementation using only GPIOs to get the switches
and LEDs working properly.

We used singleCamDet.py to understand and get familiar with coding a single camera
and tried to syncronize two cameras with syncCamDet.py, however, this was unsuccussful. 
Instead, we merged singleCamDet.py and blindspot_turnsig.py to implement bsod.py to
have the each camera turn on sequentially based on a switch that's flipped on.

### Final submission
After some hardware updates, debugging, and touch ups to make our code readable and
more efficient, we developed BlindspotObjectDetectionFinal.py as our final software
progam that meets with our goal.
