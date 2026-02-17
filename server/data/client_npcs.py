# Offset-based client NPC identification
# =========================================
# Client-side NPC entity IDs = session.clientEntID + fixed_offset
# The offsets are constant per level (baked into the SWF).
#
# Format:  { offset_from_player_id: "normalized_character_name" }
# The character_name is used to look up NPC_CHATS.

# Generic fallback for truly unknown NPCs (no offset match)
GENERIC_NPC_CHATS = [
    "Hello, adventurer!",
    "Stay safe out there.",
    "The roads have been dangerous lately.",
    "Good to see a friendly face.",
    "May your travels be safe.",
    "Have you heard the latest rumors?",
    "I've lived here my whole life.",
    "The monsters keep getting closer...",
    "We could always use more heroes.",
    "Take care of yourself, friend.",
    "It's a beautiful day, isn't it?",
    "I hope the harvest is better this year.",
    "Keep your wits about you.",
    "Adventurers pass through here all the time.",
    "Thank you for protecting us.",
    "I saw a goblin stealing chickens yesterday.",
    "Do you think the King knows what's happening out here?",
    "My feet hurt from standing all day.",
    "A storm is coming, I can feel it in my bones.",
    "Have you visited the tavern lately?",
    "Don't wander too far into the woods at night.",
    "I lost my lucky coin somewhere nearby.",
    "The blacksmith makes the finest weapons.",
    "Watch out for the old mine, it's haunted.",
    "Fresh air is good for the soul.",
    "I wish I could travel the world like you.",
    "Have you ever seen a dragon?",
    "Life is hard, but we manage.",
    "Please, help us if you can.",
    "The guards are doing their best.",
    "I'm saving up to move to the city.",
    "Do you have any tales from your travels?",
    "The sunset is unparalleled from this hill.",
    "Quiet days are the best days.",
    "Beware of strangers bearing gifts.",
    "Farming is honest work.",
    "I used to be an adventurer until I took an arrow to the knee.",
    "Magic is dangerous stuff.",
    "The spirits of the forest are restless.",
    "Keep your sword sharp and your shield ready.",
    "Nothing beats a home-cooked meal.",
    "The water in the well tastes specific today.",
    "Have you met the Mayor?",
    "I heard strange noises last night.",
    "The economy is in shambles.",
    "Do you need directions?",
    "Peace and quiet, that's all I want.",
    "Every scar tells a story.",
    "Trust no one in the shadows.",
    "Honor is more valuable than gold.",
    "The world is bigger than it looks.",
    "Don't forget to rest occasionally.",
    "A full backpack is a heavy burden.",
    "Victory favors the prepared.",
    "Legends say a hero will save us all.",
]

# ── SwampRoadNorth (Black Rose Mire) ── Halloween Event Statues
# Offsets computed from: playerID=36661, npc_ids=[1806133, 2068277, 2133813, 2199349]
# ── Robust Index-Based Map ──
# Instead of exact offsets, we map the "Index" (Offset >> 16).
# Offset 1769472 = 27 * 65536 -> Index 27
# Offset 1835008 = 28 * 65536 -> Index 28
# This is much safer against minor variations.
NPC_INDEX_MAP = {
    # SwampRoadNorth (Halloween Statues)
    27: "lubu",         # 3rd Place
    28: "clintt",       # 1st Place
    29: "purplered",    # 1st Place
    30: "jeromelin",    # 4th Place
    31: "purplered",    # Alt/Hard mode?
    32: "clintt",       # Alt/Hard mode?
    33: "jeromelin",    # Alt/Hard mode?
    
    # NewbieRoad (Village)
    # 5636096 >> 16 = 86
    86: "ehric",
    87: "anna",
    88: "mayorristas",
    89: "galrius",
    90: "tess",
    91: "tyna",
    92: "odem",
    94: "affric", # 6160384 >> 16 = 94
}
