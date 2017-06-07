# home-vision
Identify users from camera inputs based on other home automation triggers, using piped-in data (via MQTT) to further train the model automatically

<h2>The features of this program include:</h2>
<ul>
<li>Integrating with an MQTT server on the network to react based on home automation events
<li>Starting recording using a webcam when a door is opened
<li>Using a Haar cascade to identify potential faces in an image
<li>Running a Fisher face recognizer, trained based on other home automation data, to identify who has entered the home through any of the monitored doors
</ul>

<h2>Sources of data:</h2>
<table><tr>
<td>Door opening/closing</td><td>Reed switch on all external doors, hooked into a Raspberry Pi at a central location</td>
</tr>
<tr>
<td>User presence in the home</td><td>Node.JS process running which scrapes the Wi-Fi router's admin page to determine if the user's phone's MAC is connected.  This input is routed through Homeseer and relayed via a MQTT plugin</td>
</tr>
<tr>
<td>Camera inputs</td><td>Webcams and Raspi cams attached to devices on the network</td>
</tr>
<tr>
<td>MQTT server</td><td>Running on a Raspberry Pi on the network</td>
</tr>
</table>

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
