# Robot Car v3

## Objectives:
### P0: no obstacles
* robot car can drive towards a static target
* robot car can follow a moving target
### P1: obstacles
* robot car can drive towards a static target *redirecting when bumping into obstacles*
* robot car can follow a moving target *redirecting when bumping into obstacles*
### P2: obstacle avoidance
* robot car can drive towards a static target *avoiding obstacles*
* robot car can follow a moving target *avoiding obstacles*

## Robot Design
### P0:
* vacuum Robot Style: circular, 2 main wheels, caster wheels front and back
* camera Holder (looking to the front)
* battery holders for 9V battery (and powerbank? Small one?)
### P1:
* front: button bar to detect contact - 3 separate buttons: half-left, front, half-right
* expand adding Sonic Senor & Compass for Self-Localization
### P2:
* laser distance sensors for more accurate detection of obstacles in front & self-localization

![](./sketch.jpg)
![](./car1.jpg)

## Self-Driving capabilities
### P0:
* drive towards a defined object - object detection - correct steering to keep object in center (single object)
* adjust directions for moving targets
### P1:
* when detecting an obstacle (bumping into - detect obstacle direction with 3 button setup) - drive around (pre-programmed manoeuvers)
### P2:
* drive to defined position, obstacle avoidance (using sensors)
* path finding - drive towards object but account for obstacles
* internal mapping - given a room map (and the current position) - drive towards a position

## Design & Building
* wheel holders
* space for boards (Raspberry Pi & controller shield) - buy screws?
* cardboard model first?

![](./car1top.jpg)