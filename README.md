# Blindspot Object Detection
### Our goal
In this repository, my team, Team Echo, developed a final version of our Blindspot 
Object Detection system that uses two cameras supported by the NVIDIA Jetson Nano 
microcontroller to alerts drivers of objects in their blindspot via LEDs.

### Simulation
First, we simulated a scenerio of a car driving and switching lanes near other
cars. A camera was placed on each side of the car and proved to detect objects in 
the cars blindspot.

### Implementation
blindspot_turnsig.py is our first implementation using only GPIOs to get the switches
and LEDs working properly.

We used singleCamDet.py to understand and get familiar with coding a single camera
and tried to syncronize two cameras with syncCamDet.py, however, this was unsuccussful. 
Instead, we merged singleCamDet.py and blindspot_turnsig.py to implement bsod.py that runs
the two camers sequentially depending on a switch that's flipped on.

### Final submission
We developed BlindspotObjectDetectionFinal.py as our final software progam that meets 
with our goal. This final submission supports hardware updates and was extensively debugged
and edited to make our code readable and more efficient.
