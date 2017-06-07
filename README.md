# home-vision
Process multiple camera input based on other home automation triggers

Here's an example log of the program running:
<pre>
2017-06-07 02:55:52,363 face-processor INFO - Training face recognizer...
2017-06-07 02:55:52,364 face-processor INFO - Processing room kitchen user spencer
2017-06-07 02:55:52,378 face-processor INFO - Processing room kitchen user stacy
2017-06-07 02:55:52,381 face-processor INFO - Training for room kitchen
2017-06-07 02:55:52,390 face-processor INFO - Images: 34
2017-06-07 02:55:52,607 face-processor INFO - Done
2017-06-07 02:55:52,621 arrival-processor INFO - mqtt connected: 0
2017-06-07 02:56:09,911 arrival-processor INFO - Processing door (100)
2017-06-07 02:56:09,911 arrival-processor INFO - Starting capture for kitchen
2017-06-07 02:56:09,912 face-capture INFO - Starting video capture for kitchen door
2017-06-07 02:56:10,135 face-capture INFO - Camera open, proceeding with capture
2017-06-07 02:56:11,970 arrival-processor INFO - Processing door (0)
2017-06-07 02:56:19,809 face-capture INFO - Video capture complete (6.22 seconds, 8 frames)
2017-06-07 02:56:19,824 face-capture INFO - User identified: spencer
2017-06-07 02:56:33,766 arrival-processor INFO - Processing presence for spencer - home
Moving kitchen-e1dd70ce-4b2c-11e7-9299-b827eb09c8e1.jpg to users/spencer/kitchen
Moving kitchen-e1dedd38-4b2c-11e7-9299-b827eb09c8e1.jpg to users/spencer/kitchen
Moving kitchen-b944b90c-4b2b-11e7-a8ea-b827eb09c8e1.jpg to users/spencer/kitchen
Moving kitchen-b946602c-4b2b-11e7-a8ea-b827eb09c8e1.jpg to users/spencer/kitchen
Moving kitchen-b945d274-4b2b-11e7-a8ea-b827eb09c8e1.jpg to users/spencer/kitchen
Moving kitchen-e1de94c2-4b2c-11e7-9299-b827eb09c8e1.jpg to users/spencer/kitchen
Moving kitchen-b9461b26-4b2b-11e7-a8ea-b827eb09c8e1.jpg to users/spencer/kitchen
</pre>
I had prepopulated the users/spencer/kitchen and users/stacy/kitchen folders with images from test runs.  This allowed the face recognizer to be trained for this run.
