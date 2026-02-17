# Bubble chats for NewbieRoad NPCs
# Keys: Normalized NPC names (matches handle_talk_to_npc logic)
# Values: List of strings to be picked randomly

NPC_CHATS = {
    # Captain Fink
    "captainfink": [
        "We need to find that village.",
        "You can find the village on the map.",
        "Just head east and you'll find it.",
        "I'll try to repair the Niobe.",
        "I must get word to the king!",
        "I'm amazed there are still humans here.",
        "The sea goblins were running from something...",
        "We made it to shore alive, at least.",
        # Mission 1 intro
        "Land ho! All hands on deck!",
        "Defend the ship! Don't let them aboard!",
    ],
    
    # TutorialBoat parrot (Pecky) - Mission 1 specific
    "tutorialboatparrot": [
        "Squawk! Goblins! Goblins everywhere!",
        "Squawk! Help! We're under attack!",
        "Squawk! The goblins are boarding!",
    ],
    
    "introparrot": [
        "Squawk! Goblins! Goblins everywhere! Help Pecky!",
        "Squawk! Help! Anna is trapped!",
        "Squawk! Greedy goblins! Greedy goblins!",
        "Squawk! They dragged Anna deeper inside! Follow Pecky!",
        "Squawk! Pecky knows the way! This way!",
        "Squawk! Bad goblins took the pretty lady!",
        # Mission 3 - Anna freed
        "Squawk! Anna is free! Pecky helped!",
    ],
    
    "finkbird": [
        "Squawk! Goblins! Goblins everywhere! Help Pecky!",
        "Squawk! Help! Anna is trapped!",
        "Squawk! Greedy goblins! Greedy goblins!"
    ],

    # Mayor of Wolf's End (NR_Mayor01) - Mission 2 & 5 specific
    "nrmayor01": [
        "Thanks to hard fighters like Anna, we've held our own.",
        "We came over with Sigismund Hocke fifty years ago.",
        "Fifty years ago we had Wolf's End Keep to protect us.",
        "Sigismund Hocke built the keep as a base for his expedition.",
        "Goblins and worse drove us out decades ago.",
        "Our fighters need their leader.",
        "This village will be the first of several we reclaim.",
        "With Wolf's End secure, we can reclaim more of the land from evil.",
        "We will fortify our camp here, hero.",
        "My thanks for leading us.",
        # Mission 2: MeetTheTown - Welcome to Wolf's End
        "It cannot be! Has someone from the homeland finally returned to Ellyria?",
        "Thank the heavens you've arrived!",
        # Mission 5: ClearYourHouse - I Claim This Keep
        "Fifty years ago we had Wolf's End Keep to protect us.",
    ],

    # Anna (NR_QuestAnna01, NR_QuestAnna02, NR_QuestAnna03, Anna)
    "anna": [
        "Thank you for freeing me!",
        "Our fighters need their leader.",
        "Someone named 'Nephit' is trying to control the goblins.",
        "My father read through the old reports from when we landed 50 years ago.",
        "There is another tomb. Maybe what Nephit sought is in there.",
        "A dragon! Amazing, even if it’s only a kind of dream phantom.",
        "With Nephit driven off, maybe we'll have fewer undead and goblins both."
    ],
    "nrquestanna01": [
         "Someone named 'Nephit' is trying to control the goblins.",
         "We've seen a lot of undead coming from the Tomb of the Slumbering King.",
         "Baron Hocke employed the wisest men in the world for his research."
    ],
    "nrquestanna02": [
        "There is another tomb. Maybe what Nephit sought is in there.",
        "Nephit might've wanted dragon bones.",
        "The tomb is to the south, through the woods."
    ],
    "nrquestanna03": [
         "With Wolf's End secure, we can reclaim more of the land from evil.",
         "We've got a lot of hard fighting ahead, but we can do it.",
         "This whole land was once green pasture."
    ],

    # Villagers
    "nrvillager02": [
        "Goblins stole all our horseshoes and made noserings.",
        "The big goblins wear horseshoes as noserings.",
        "If there were fewer goblins, we could reclaim this land.",
        "I haven't seen the goblins this excited in years.",
        "You're one tough goblin fighter.",
        "This place might be saved yet."
    ],

    "nrvillager03": [
        "The goblin shamans use their wands to control Death Eyes.",
        "It will be nice not to have those evil things spying on us.",
        "I hate the way those Death Eyes look at me.",
        "Thanks again for your help."
    ],
    
    "nrcartguy": [
        "There are goblin raiders holed up in that farm.",
        "We've got the trogs cornered.",
        "You've got the goblins on the run.",
        "As long as we keep up the pressure...",
        "We can reclaim this land."
    ],

    "nrhermit": [
        "The undead just keep rising from that crypt.",
        "The old shrine up there is where the undead first came from.",
        "They've been coming ever since.",
        "I'll keep fighting them.",
        "I'll never get used to their smell."
    ],

    # BridgeTown / Felbridge NPCs
    "npcfelbridgerichan": [
        "Welcome to Felbridge, traveler.",
        "The swamps have been dangerous lately.",
        "Be careful if you head north.",
        "The bridge connects us to the rest of the world.",
        "We see many adventurers pass through here."
    ],
    "npctraveller": [
        "I've come a long way to see the sights.",
        "Do you know the way to the capital?",
        "My feet are killing me.",
        "This town is a nice place to rest.",
        "I heard rumors of a dragon nearby."
    ],
    "npcvillager01": [
        "Good day to you.",
        "Are you here to help with the monsters?",
        "The crops aren't doing well this year.",
        "My son wants to be an adventurer like you.",
        "Stay safe out there."
    ],
    "npcvillager05": [
        "I saw something strange in the woods.",
        "Have you seen the mayor?",
        "We need more guards.",
        "The nights are getting colder.",
        "I hope the harvest is good."
    ],
    "npcswampvillager07": [
        "The swamp waters are rising.",
        "Watch out for the biting flies.",
        "It's humid today, isn't it?",
        "I found a strange flower yesterday.",
        "Don't wander off the path."
    ],
    "npcvillager08": [
        "Hello there!",
        "Do you like my dress?",
        "I'm waiting for a package.",
        "The market is busy today.",
        "Have a wonderful day."
    ],
    "npcswampvillager03": [
        "Need some training?",
        "A strong arm is better than a sharp sword.",
        "Keep your guard up.",
        "Action is the key to success.",
        "Don't let them get behind you."
    ],
    "npcswampoldman01": [
        "In my day, we didn't have these problems.",
        "The spirits are restless.",
        "Values these days...",
        "I remember when this was all fields.",
        "Listen to your elders."
    ],
    "npcswampvillager05": [
        "Fishing is good today.",
        "Caught a big one yesterday.",
        "The water is murky.",
        "Need bait?",
        "Quiet, you'll scare the fish."
    ],
    "npcvillager09": [
        "Hammer and tongs, that's my life.",
        "Need something fixed?",
        "Iron is strong, but steel is stronger.",
        "The forge is hot today.",
        "Quality work takes time."
    ],
    "npcswampvillager09": [
        "My garden is ruined.",
        "Those pests ate my vegetables.",
        "Help me chase them away?",
        "Fresh produce for sale.",
        "Nature can be cruel."
    ],
    "npcswampvillager08": [
        "Have you seen my cat?",
        "I love this town.",
        "The air smells fresh.",
        "Are you new here?",
        "Let's be friends."
    ],
    "npcvillager04": [
        "Best goods in the realm!",
        "Buy one, get one... for full price!",
        "Rare items for sale.",
        "Everything must go.",
        "Looking for something special?"
    ],
    "npcwarden": [
        "Halt! Who goes there?",
        "Keep the peace.",
        "No trouble on my watch.",
        "Move along, citizen.",
        "The law is absolute."
    ],
    "npcswampvillager09a": [
        "Sing a song with me?",
        "I love to dance.",
        "Isn't the sky beautiful?",
        "Let's play a game.",
        "Joy is everywhere."
    ],
    "npcfelbridgeguard": [
        "Stay vigilant.",
        "Protect the bridge.",
        "Report any suspicious activity.",
        "For the King!",
        "Duty calls."
    ],
    "meylourmagenpc": [
        "The arcane energies are strong here.",
        "I sense a disturbance.",
        "Magic is not a toy.",
        "Knowledge is power.",
        "Seek the truth."
    ],
    "meylourmagenpc2": [
        "My experiments are delicate.",
        "Don't touch anything.",
        "The stars align.",
        "A fascinating specimen.",
        "Ah, another seeker of wisdom."
    ]
}

# CraftTown NPCs
NPC_CHATS.update({
    "npcappraiser": [
        "Gold is the only truth.",
        "Everything has a price.",
        "I can tell you exactly what that's worth.",
        "A fine specimen indeed.",
        "Bring me something rare."
    ],
    "npcmagicshop": [
        "Potions for every ailment.",
        "Magic flows through everything.",
        "Careful with that flask.",
        "Looking for power?",
        "My brew is the strongest in the land."
    ],
    "npcpetshop": [
        "All creatures need love.",
        "Adopt a friend today.",
        "They are loyal if you treat them right.",
        "Have you fed your pet?",
        "This one likes to bite."
    ],
    "npcbanker": [
        "Your goods are safe with us.",
        "Security is our priority.",
        "Storage space is available.",
        "Trust in the vault.",
        "Deposits only today."
    ],
    "npccrafttownvillager": [
        "It's a peaceful day.",
        "The air is clean here.",
        "Welcome to our town.",
        "Have you visited the forge?",
        "I love the view from here."
    ]
})

# SwampRoad NPCs
NPC_CHATS.update({
    "npcswampvillager01": [
        "The mist hides many secrets.",
        "Don't lose your way.",
        "The swamp takes those who wander.",
        "I heard a scream last night.",
        "Stay on the path."
    ],
    "npcswampvillager02": [
        "Mosquitoes are huge this year.",
        "My boots are soaked.",
        "Looking for the bridge?",
        "Watch out for the trolls.",
        "Damp and dreary, just how I like it."
    ],
    "npcswampguard": [
        "Halt! State your business.",
        "The road is dangerous.",
        "Monsters lurk in the shadows.",
        "We protect travelers.",
        "Keep your weapon ready."
    ]
})

# Shazari Desert NPCs
NPC_CHATS.update({
    "npcdesertvillager01": [
        "Water is life.",
        "The sun is unforgiving.",
        "Seek shade, traveler.",
        "The sands shift constantly.",
        "Have you seen the oasis?"
    ],
    "npcnomad": [
        "The desert is my home.",
        "We move with the wind.",
        "The stars guide us.",
        "Trade is the lifeblood of the desert.",
        "May your journey be cool."
    ],
    "npcdesertmerchant": [
        "Exotic goods from afar.",
        "Spices, silks, and gems.",
        "A fair price for a fair trade.",
        "You won't find this anywhere else.",
        "Take a look at my wares."
    ]
})

# Jade City NPCs
NPC_CHATS.update({
    "npcjadeguard": [
        "The Emperor watches over us.",
        "Order must be maintained.",
        "Respect the laws.",
        "Valhaven is the jewel of the East.",
        "Stand aside."
    ],
    "npcmonk": [
        "Inner peace is the true strength.",
        "Balance in all things.",
        "Meditation clears the mind.",
        "The spirit is stronger than the body.",
        "Walk the path of enlightenment."
    ],
    "npcjadecitizen": [
        "The festivals are beautiful.",
        "Have you visited the temple?",
        "The gardens are blooming.",
        "Prosperity to you.",
        "Welcome to Jade City."
    ]
})

# OldMineMountain (Stormshard) NPCs
NPC_CHATS.update({
    "shamar": [
        "The mountain pass is treacherous.",
        "Rock Hulks are everywhere.",
        "Watch your step.",
        "I'm scouting the area.",
        "Don't disturb the elements."
    ],
    "adohi": [
        "Welcome to Stormshard.",
        "The spirits of the mountain are restless.",
        "We live in harmony with the stone.",
        "Beware the deep mines.",
        "May the earth protect you."
    ],
    "npcvillager02": [
        "Training is hard at this altitude.",
        "Breathe deeply.",
        "Focus your energy.",
        "The mountain tests us all.",
        "Strength comes from within."
    ],
    "ormos": [
        "I found a rare gem yesterday.",
        "The mining is difficult work.",
        "These rocks are older than time.",
        "Have you seen the crystal caves?",
        "Safety first."
    ],
    "amilie": [
        "The view is breathtaking.",
        "It's cold up here.",
        "I love the sound of the wind.",
        "Are you cold?",
        "Stormshard is beautiful."
    ],
    "npcmoai": [
        "...",
        "*Rumble*",
        "The stone watches.",
        "Ancient whispers...",
        "*Silence*"
    ],
    "npcvillager06": [
        "Did you hear that rumble?",
        "Avalanches are common.",
        "Keep your voice down.",
        "The yeti is just a myth... right?",
        "I need a warm drink."
    ]
})

# NewbieRoad client-side NPCs (baked into Flash SWF)
NPC_CHATS.update({
    "ehric": [
        "Living out here toughens you up.",
        "Watch out for wolves near the old road.",
        "It's not safe to travel alone after dark.",
        "I've been in these parts for years.",
        "If you're heading east, be careful.",
    ],
    "mayorristas": [
        "Our village might be small, but we are strong.",
        "The goblins have been more aggressive lately.",
        "We need brave heroes to protect these lands.",
        "I do what I can for the people here.",
        "Stay a while, adventurer. You're safe here.",
    ],
    "galrius": [
        "The old kingdom once stretched to the horizon.",
        "I've seen things in these woods that would haunt you.",
        "Keep your blade sharp and your eyes sharper.",
        "The land remembers what we have forgotten.",
        "Trust your instincts out there.",
    ],
    "tess": [
        "I gather herbs from the hillside every morning.",
        "These lands used to be greener.",
        "My grandmother told stories of the old days.",
        "It's a quiet life, but it's ours.",
        "Would you like some fresh bread?",
    ],
    "tyna": [
        "The weather is changing... I can feel it.",
        "Have you come far, traveler?",
        "I hope the harvest is better this year.",
        "My children keep asking about adventurers.",
        "Be kind to the animals, will you?",
    ],
    "odem": [
        "I keep watch over the road at night.",
        "Something stirs in the old ruins to the south.",
        "Did you see those lights last night?",
        "I used to be a soldier, you know.",
        "Stay sharp, friend.",
    ],
    "affric": [
        "I trade goods with the villages down the road.",
        "Business has been slow with all these monsters about.",
        "Need supplies? I might have what you need.",
        "The roads aren't safe for merchants anymore.",
        "A good sword is worth its weight in gold.",
    ],
})

# SwampRoadNorth (Black Rose Mire) — Halloween Event Statue NPCs
# FlavorText dialogues from Game.swz.txt
NPC_CHATS.update({
    "clintt": [
        "First Place, Clintt.",
        "Her mastery of magic...",
        "And prowess with a staff.",
        "Shamed the Green Knight...",
        "And gave her the last laugh.",
    ],
    "purplered": [
        "First Place, PurpleRed.",
        "With arcane power and skill...",
        "The Green Knight did she slay.",
        "Now Purple and Red...",
        "Are the colors of the day.",
    ],
    "lubu": [
        "Third Place, LuBu.",
        "With divine might in his arms...",
        "And holy vengeance in his swing...",
        "LuBu cut down the Green Knight.",
        "For glory and his King.",
    ],
    "jeromelin": [
        "Fourth Place, JeromeLin.",
        "From the shadows he struck...",
        "His blade quick and true.",
        "JeromeLin beat the Green Knight...",
        "Many more time than did you.",
    ],
})

# ── BridgeTown (Starting Town) ──
NPC_CHATS.update({
    "gretta": [
        "Welcome to BridgeTown, traveler.",
        "The bridge has seen better days.",
        "Watch out for the river trolls.",
        "My husband is out fishing... again.",
        "It's a peaceful life here, mostly.",
    ],
    "grettahard": ["The river currents are strong today.", "Fishermen say something's in the deep.", "Be careful near the water's edge.", "We rely on the fish for trade.", "Have you seen any strange creatures?"],
    
    "smiddy": [
        "Need a new blade? I've got the best steel.",
        "Hammering all day keeps you strong.",
        "The heat of the forge never bothers me.",
        "A sharp sword is your best friend.",
        "Don't let rust settle on your armor.",
    ],
    "smiddyhard": ["Iron from the old mines is scarce.", "I can fix that dent in your shield.", "Quality craftsmanship takes time.", "My father taught me this trade.", "The anvil rings true today."],

    "kenelm": [
        "I saw a strange light in the forest.",
        "Do you think the legends are true?",
        "I was an adventurer once, like you.",
        "My knees aren't what they used to be.",
        "Stay on the path, friend.",
    ],
    "kenelmhard": ["The woods are darker than usual.", "Old tales speak of hidden treasures.", "Beware the shadows.", "I miss the thrill of the hunt.", "Be wary of wolves."],

    "laura": [
        "Have you seen my cat?",
        "It's a lovely day for a walk.",
        "The flowers are blooming early this year.",
        "Be polite to your elders.",
        "Would you like some tea?",
    ],
    "laurahard": ["The wind carries whispers tonight.", "I planted these herbs myself.", "Kindness costs nothing.", "A smile brightens the day.", "Do you know any songs?"],

    "lucy": [
        "I want to be a hero when I grow up.",
        "Can you teach me how to fight?",
        "My brother is annoying.",
        "I found a shiny rock!",
        "Do goblins eat people?",
    ],
    "lucyhard": ["Look what I found!", "Are you strong?", "Tell me a story!", "I'm not scared of anything!", "Let's play hide and seek!"],
})


# ── Emerald Glades (Forest Region) ──
NPC_CHATS.update({
    "sugh": [
        "The forest speaks if you listen.",
        "Do not disturb the natural order.",
        "The spirits are restless.",
        "Walk softly upon the earth.",
        "Nature provides for those who respect it.",
    ],
    "sughhard": ["The roots run deep here.", "Ancient magic lingers in the air.", "Protect the groves.", "Listen to the wind.", "Harmony must be maintained."],

    "emma": [
        "The glades are beautiful in the spring.",
        "Watch out for the spiders.",
        "I gather berries for the village.",
        "Have you been to the Great Tree?",
        "The air is so fresh here.",
    ],
    "emmahard": ["The shadows lengthen.", "Something moved in the brush.", "Stay close to the light.", "The forest has eyes.", "Be wary of the deep woods."],

    "earl": [
        "Chopping wood is honest work.",
        "These trees are older than kingdoms.",
        "Don't wander off the path.",
        "Seen any elves lately?",
        "Need some firewood?",
    ],
    "earlhard": ["The timber is tough this season.", "Axes need sharpening.", "Hard work builds character.", "Use the right tool for the job.", "Respect the forest."],

    "dane": [
        "I track game through these woods.",
        "Silence is your best weapon.",
        "The wind changed direction.",
        "I saw tracks near the river.",
        "Stay downwind if you're hunting.",
    ],
    "danehard": ["Prey is scarce.", "Something big passed through here.", "Keep your eyes open.", "Trust your instincts.", "The hunter becomes the hunted."],

    "franny": [
        "My garden is my pride and joy.",
        "Don't step on the flowers!",
        "Bees are buzzing today.",
        "Fresh vegetables are the best.",
        "Watering plants is hard work.",
    ],
    "frannyhard": ["The soil is rich here.", "Plants need love too.", "Green thumbs run in the family.", "Look at this bloom!", "Nature is wonderful."],
})

# ── Old Mine Mountain (Dwarven/Mining Region) ──
NPC_CHATS.update({
    "yolaf": [
        "The mountain holds many secrets.",
        "Dig deep enough and you'll find trouble.",
        "Gold isn't the only thing down there.",
        "Watch your step on the cliffs.",
        "The mines have been closed for years.",
    ],
    "yolafhard": ["Echoes in the deep...", "The stone remembers.", "Dark things dwell below.", "Keep your lantern lit.", "Don't get lost."],

    "ian": [
        "It's cold up here on the peak.",
        "The view is worth the climb.",
        "I prefer the open sky to the mines.",
        "Seen any yetis?",
        "Bundle up, traveler.",
    ],
    "ianhard": ["The wind bites.", "Snow is coming.", "The summit is treacherous.", "Frostbite is no joke.", "Keep moving to stay warm."],

    "hooch": [
        "A good drink warms the bones.",
        "Cheers to another day alive!",
        "Have you tried the local brew?",
        "Sing a song with us!",
        "Life is too short to be sober.",
    ],
    "hoochhard": ["Another round!", "Raise your tankard!", "Here's to health and wealth!", "Don't spill a drop.", "Good company, good times."],

    "hook": [
        "Lost an eye in a goblin raid.",
        "These scars tell stories.",
        "I've fought more battles than you've had hot meals.",
        "Never turn your back on an enemy.",
        "Pain is a good teacher.",
    ],
    "hookhard": ["War never changes.", "Keep your guard up.", "Expect the unexpected.", "Survival of the fittest.", "Victory comes at a cost."],

    "gunther": [
        "Mining is dangerous work.",
        "We found a new vein of ore.",
        "Explosives are unstable.",
        "Check your gear before going down.",
        "Rock and stone!",
    ],
    "guntherhard": ["The earth trembles.", "Cave-ins are a risk.", "We dig for riches.", "Strike the earth!", "Fortunes are made below."],

    "gale": [
        "The winds howl through the canyons.",
        "I collect rare stones.",
        "This place is haunted by the past.",
        "Did you hear the whispers?",
        "The mountain demands respect.",
    ],
    "galehard": ["Storms brew quickly here.", "High altitude makes you dizzy.", "Watch for falling rocks.", "The peaks are unforgiving.", "Nature is powerful."],
})

# ── Shazari Desert (Desert Region) ──
NPC_CHATS.update({
    "rose": [
        "The desert heat is unforgiving.",
        "Water is more precious than gold here.",
        "Beware the sandstorms.",
        "Ancient ruins lie buried beneath the dunes.",
        "Travel by night if you can.",
    ],
    "rosehard": ["The sun beats down.", "Mirages can deceive you.", "Keep your waterskin full.", "The sands shift constantly.", "Seek shelter at noon."],

    "palok": [
        "I trade spices and silks.",
        "Looking for a bargain?",
        "My camel is stubborn today.",
        "The bazaar is full of wonders.",
        "Coin is the language of the world.",
    ],
    "palokhard": ["Fair prices for fair goods.", "See what I have in stock.", "Rare items from afar.", "Trade is the lifeblood of cities.", "Everything has a price."],

    "jema": [
        "The stars guide us across the sands.",
        "Nomadic life is freedom.",
        "We follow the ancient paths.",
        "The desert has its own beauty.",
        "Respect the oasis.",
    ],
    "jemahard": ["The night sky is clear.", "Follow the North Star.", "Sand in your boots is inevitable.", "The dunes sing at night.", "Endurance is key."],

    "kala": [
        "Scorpions hide in the shade.",
        "Snake venom is potent.",
        "Watch where you step.",
        "Survival is a daily struggle.",
        "The desert takes the weak.",
    ],
    "kalahard": ["Heatstroke is a silent killer.", "Find shade where you can.", "Conserve your energy.", "Nature is harsh.", "Adapt or perish."],

    "sadie": [
        "I search for lost artifacts.",
        "The ancients knew powerful magic.",
        "History is written in stone.",
        "Uncover the past to understand the future.",
        "Knowledge is power.",
    ],
    "sadiehard": ["Ruins hold many traps.", "Deciphering the glyphs.", "Ancient curses are real.", "Digging for truth.", "The past never dies."],
})

# ── Swamp Road (Swamp Region) ──
NPC_CHATS.update({
    "rodgert": [
        "The swamp is full of disease.",
        "Don't stray from the boardwalk.",
        "Mosquitoes are fierce tonight.",
        "Seen any giant reptiles?",
        "The mist hides many things.",
    ],
    "rodgerthard": ["Damp and dreary.", "The smell of rot.", "Watch for sinking mud.", "Something slithers nearby.", "Keep your boots dry."],
})


# ── Jade City (Eastern/Asian Theme) ──
NPC_CHATS.update({
    "kasa": [
        "Discipline is the key to strength.",
        "Honor your ancestors.",
        "The blade is an extension of the soul.",
        "Patience, young grasshopper.",
        "Balance in all things.",
    ],
    "kasahard": ["Meditation clears the mind.", "Focus your chi.", "Strike with precision.", "Defend the weak.", "Martial arts are a way of life."],

    "kevah": [
        "The Emperor watches over us.",
        "Order must be maintained.",
        "Respect the law.",
        "Duty before self.",
        "Protect the city.",
    ],
    "kevahhard": ["Vigilance is required.", "Report suspicious activity.", "The walls are strong.", "We serve the people.", "Peace through strength."],

    "kohken": [
        "Do you seek wisdom?",
        "The tea ceremony is sacred.",
        "Silence speaks volumes.",
        "Observe the falling leaves.",
        "Inner peace is the true victory.",
    ],
    "kohkenhard": ["The path is long.", "Enlightenment takes time.", "Listen to the river.", "Nature teaches us.", "Simplicity is elegant."],

    "rakka": [
        "Dragons once ruled these skies.",
        "Legends are born here.",
        "Firecrackers scare away evil spirits.",
        "Celebrations are important.",
        "Joy brings good fortune.",
    ],
    "rakkahard": ["Believe in magic.", "Stories keep us alive.", "Look to the horizon.", "Hope is powerful.", "Dreams can come true."],

    "wutu": [
        "Hard work brings prosperity.",
        "Rice fields need tending.",
        "The harvest will be bountiful.",
        "Community is everything.",
        "Help your neighbor.",
    ],
    "wutuhard": ["Rain is a blessing.", "The seasons change.", "Life follows a cycle.", "Gratitude for the land.", "Work together."],
    
    "norgog": [
        "Me smash good!",
        "Norgog strong!",
        "You give shiny?",
        "Big monster scary.",
        "Norgog hungry.",
    ],
    "norgoghard": ["Me protect friend.", "Where food?", "Sleep now.", "Sun warm.", "Rock heavy."],
})

# ── Generic/Common NPC Types ──
# These keys are used when specific numbered NPCs (e.g. Villager01) don't have
# a specific entry. The server strips numbers to find these base keys.
NPC_CHATS.update({
    "villager": [
        "Nice weather we're having.",
        "I hope the harvest is good.",
        "Have you heard the news?",
        "Working hard or hardly working?",
        "Stay safe out there.",
    ],
    "citizen": [
        "The city guards are doubled today.",
        "Taxes are high this year.",
        "I'm late for a meeting.",
        "Have you been to the market?",
        "City life is busy.",
    ],
    "merchant": [
        "Best prices in the realm!",
        "Fresh goods, just arrived!",
        "Can I interest you in something?",
        "I have rare items from the east.",
        "Business is good.",
    ],
    "trainer": [
        "Keep your guard up!",
        "Again! With more feeling!",
        "Pain is weakness leaving the body.",
        "Focus on your breathing.",
        "You have potential, recruit.",
    ],
    "guard": [
        "Move along, citizen.",
        "No trouble on my watch.",
        "Stay out of trouble.",
        "I used to be an adventurer like you.",
        "Keep your weapons sheathed.",
    ],
    "imperialguard": [
        "For the Emperor!",
        "Halt! Who goes there?",
        "We serve the Empire.",
        "Order must be maintained.",
        "Report any suspicious activity.",
    ],
    "monk": [
        "Peace be with you.",
        "The mind must be clear.",
        "Violence is a last resort.",
        "Meditate on your actions.",
        "Balance is key.",
    ],
    "acolyte": [
        "The spirits guide us.",
        "I must finish my prayers.",
        "The temple is open to all.",
        "Do you seek healing?",
        "Faith is our shield.",
    ],
    "nomad": [
        "The wind calls my name.",
        "We travel with the seasons.",
        "Home is where the heart is.",
        "The road is long.",
        "Share a meal with us.",
    ],
    "slave": [
        "Work, work, work.",
        "Keep your head down.",
        "Don't look the guards in the eye.",
        "One day we will be free.",
        "Hunger is a constant companion.",
    ],
})

# ── Regional Variants ──
# Mapping region-prefixed generic types to dialogues
NPC_CHATS.update({
    # NewbieRoad
    "nrvillager": NPC_CHATS["villager"],
    "nrmerchant": NPC_CHATS["merchant"],
    "nrtrainer": NPC_CHATS["trainer"],
    
    # Emerald Glades
    "egvillager": NPC_CHATS["villager"],
    "egmerchant": NPC_CHATS["merchant"],
    "egtrainer": NPC_CHATS["trainer"],
    "egscout": NPC_CHATS["guard"],
    
    # Old Mine Mountain
    "ommvillager": NPC_CHATS["villager"],
    "ommmerchant": NPC_CHATS["merchant"],
    "ommtrainer": NPC_CHATS["trainer"],
    "ommscout": NPC_CHATS["guard"],
    
    # Shazari Desert
    "sdnomad": NPC_CHATS["nomad"],
    "sdmerchant": NPC_CHATS["merchant"],
    "sdtrainer": NPC_CHATS["trainer"],
    "sdslave": NPC_CHATS["slave"],
    
    # Swamp Road North
    "srnmayor": NPC_CHATS["villager"],
    "srnmerchant": NPC_CHATS["merchant"],
    "srntrainer": NPC_CHATS["trainer"],
})


