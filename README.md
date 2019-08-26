# alexa-youtube
**Unofficial YouTube skill for Alexa**

## Skill is no longer full
* This skill has become so popular, I am close to hitting the limits on the free AWS lambda tier, which is 800000 seconds of CPU time per month!
* If you have your own lambda instance and would like to host some of the load, please raise an issue and I will be in touch.
* Currently the ARNs in the readme belong to Rybot666

## Updates
* 2nd June 2018: The skill now handles playlists or channels where none of the videos exist (eg copyrighted deletions). It will now ask you if you want to try the next playlist or channel. If you have already created the skill, you will need to update the Interaction Model json file in your Alexa skill, ie step 7 under Setup Instructions.
* 22nd August 2018: Fixed a bug where channels turn up in video search results, eg in Play videos by The Beatles.
* 4th January 2019: Now works in 5 languages, thanks to everyone who helped!
* 1st February 2019: Live videos don't seem to be working. Have updated the list of commands.
* 3rd February 2019: Live videos fixed, for Gen 2 devices at least.

## Features
* Play audio from YouTube videos
* Play video (if supported) on live videos or if you ask for just one specific video (command 8)
* Makes a list of all the videos played, in the Alexa app

## Launching
* In English, say "Alexa, launch YouTube". 
* In German, say "Alexa, öffne YouTube". 
* In Italian, say "Alexa, avvia YouTube".
* In Spanish, say "Alexa, abrir YouTube".

## Skill Commands

1. Play a video, eg "Alexa, ask YouTube to play Gangnam Style"
2. Play a playlist, eg "Alexa, ask YouTube to play playlist Ultimate Beyonce"
3. Play a channel, eg "Alexa, ask YouTube to play channel Fall Out Boy Vevo"
4. You can replace "play" with "shuffle" to get a randomized version of the search results/channel/playlist, eg "Alexa, ask YouTube to shuffle channel Nicki Minaj"
5. Next / Previous / Start Over / Pause / Resume should all work
6. Ask what is playing by "Alexa, ask YouTube what song is playing" (or just "Alexa, can you repeat that?" should tell you)
7. Skip forward or back in the video by "Alexa, ask YouTube to skip forward/backward to/by one minute and one second"
8. Just play one video by "Alexa, ask YouTube to play one video Gangnam Style". You can switch in and out of "autoplay" mode by "Alexa, ask YouTube to turn on/off autoplay."
9. Find the current time in the video by "Alexa, ask YouTube what is the timestamp?"
10. If you want to play your own playlists, and the search feature finds other people's, if you follow the Advanced instructions below you can specify your own channel id.
11. Play related videos, by "Alexa, ask YouTube to play more like this". This is a YouTube feature, don't ask me why it plays what it plays.

Command 7 doesn't seem to work on Generation 1 Echo's, no idea why.
Commands 8, 9, 10 and 11 are only available in English at the moment.

## Known issues

1. Some videos just fail, it's not clear why, they work locally. The skill just moves to the next video on the playlist, but this can mean sometimes she announces a video that doesn't play.
2. It appears this skill only works on Amazon Echo products, not on 3rd party products that support Alexa. If you get it to work on another device, please let me know.
3. Live videos work on Gen 2 devices onwards, not on the original Gen 1 Echo.

## Setup Instructions

1. Go to the Alexa Console (https://developer.amazon.com/alexa/console/ask)
2. If you have not registered as an Amazon Developer then you will need to do so. Fill in your details and ensure you answer "NO" for "Do you plan to monetize apps by charging for apps or selling in-app items" and "Do you plan to monetize apps by displaying ads from the Amazon Mobile Ad Network or Mobile Associates?"
3. Once you are logged into your account click "Create Skill" on the right hand side.
4. Give your skill any name, eg "My YouTube Skill".
5. **Important** Set the language to whatever your Echo device is set to. If you are not sure, go to the Alexa app, go to Settings, Device Settings, then click on your Echo device, and look under Language. If your Echo is set to English (UK), then the skill must be English (UK), other types of English will not work!
6. Choose "Custom" as your model, and "Provision Your Own" as your method, then click "Create Skill". On the template page, choose "Start from scratch".
7. On the left hand side, click "JSON Editor".
8. Delete everything in the text box, and copy in the text from https://raw.githubusercontent.com/ndg63276/alexa-youtube/master/InteractionModel_en.json, (or use InteractionModel_fr.json, InteractionModel_it.json, InteractionModel_de.json, InteractionModel_es.json for French, Italian, German or Spanish)
9. Click "Save Model" at the top.
10. Click "Interfaces" in the menu on the left, and enable "Audio Player" and "Video App". Click "Save Interfaces".
11. Click "Endpoint" in the menu on the left, and select "AWS Lambda ARN". Under "Default Region", put ~~my ARN~~ `arn:aws:lambda:us-west-2:827204026059:function:YouTube` or the ARN you get from the section "Deploying Yourself" below.
12. Click "Save Endpoints"
13. Click "Permissions", at the very bottom on the left.
14. Turn on "Lists Read" and "Lists Write".
15. Click "Custom" in the menu on the left.
16. Click "Invocation" in the menu on the left.
17. If you want to call the skill anything other than "youtube", change it here. Click "Save Model" if you change anything.
18. Click "Build Model". This will take a minute, be patient. It should tell you if it succeeded.
19. **Important:** At the top, click "Test". Where it says "Test is disabled for this skill", change the dropdown from "Off" to "Development". 

## Keeping a list of what you have played
This skill can make a list of the last 90 videos played, but you have to give it permissions in the Alexa app:
1. Go to the Alexa app on your phone. In the menu, go to "Skills & Games", then "Your Skills", then scroll to the right and click on "Dev".
2. Click on your YouTube skill. You should see a button marked "Settings", click that. 
3. Then press on "Manage Settings", and tick the boxes marked "Lists Read Access" and "Lists Write Access", and press "Save Settings".
4. Say "Alexa, launch YouTube", that will create the list, and from then on, videos will be added to it.
The list can be viewed in the Alexa app, click Lists from the main menu.

That's it!

## Deploying yourself (optional)
This skill currently runs on my and Rybot's Lambda instance, hopefully it won't get too popular. If you want to, and know how, you can deploy it on your own Lambda, you just need the lambda_function.zip file, and a YouTube developer key. (See [here](https://www.slickremix.com/docs/get-api-key-for-youtube/)).

[tal9000v2](https://github.com/tal9000v2) has put together a handy guide for deploying yourself [here](https://github.com/ndg63276/alexa-youtube/wiki/Running-your-own-lambda-instance).

If you have (public) playlists that you would like to play, first get your channel ID from youtube. Find a video you have uploaded, then click on your name beneath it, it should take you to eg https://www.youtube.com/channel/UCDVYQ4Zhbm3S2dlz7P1GBDg, in which case your channel ID is UCDVYQ4Zhbm3S2dlz7P1GBDg. Then, when you add the environment variable DEVELOPER_KEY, add another environment variable called MY_CHANNEL_ID, with the value of that your channel ID. Then you can say, "Alexa, ask YouTube to play my playlist {name of your playlist}".

## FAQ
* **Alexa tells me she can't find any supported video skills, what does that mean?**
Alexa is trying to be too clever, and not launching this skill. Start your request by saying 'Alexa, launch YouTube' and then when she says 'Welcome to YouTube', ask for the video you want.
* **She still says she can't find any video skills.**
Make sure to follow step 19 above, enabling Testing for Development.
* **She still says she can't find any video skills!**
Try using a different word to start the skill. In English, say "Alexa, launch YouTube". In German, say "Alexa, öffne YouTube". In Italian, say "Alexa, avvia YouTube". In Spanish, say "Alexa, abrir YouTube".
* **I am getting another issue, can you fix it?**
Hopefully. Create an issue on github, with the exact wording of what you ask Alexa, so I can try and reproduce it.
* **Can you add another language?**
Yes, as long as you can translate for me. Click on 'Issues' at the top, then 'New Issue', and let me know what language you can help with, and I'll let you know what I need translating.
* **If I try and test in the Developer Console, it says 'Unsupported Directive. AudioPlayer is currently an unsupported namespace. Check the device log for more information.'**
That is normal, the Developer Console doesn't play audio. You just need to enable testing through the Developer Console, then you can use the skill through your Alexa device.
* **Why don't more videos work as video?**
Alexa doesn't provide any ability to enqueue videos, so you only get one video, then it stops. So it only plays videos if you ask for one specific video, or if it is a live video.
* **Did I hear an advert?**
Yes, that was me. If you are in the UK, and are looking for cheap, renewable energy, join Bulb using [this link](https://bulb.co.uk/refer/mark7441), and both you and me get £50 credit.
* **Why have you put in an advert?**
Writing this skill has taken a large amount of my time, and continues to do so. This is a way to support me.
You will only hear it if you are in the UK, and even then only 10% of the time (overall, it's random). If you deploy your own lambda instance, you won't hear it. 
