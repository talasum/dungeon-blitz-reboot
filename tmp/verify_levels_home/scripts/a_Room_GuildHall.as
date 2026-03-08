package
{
   import adobe.utils.*;
   import flash.accessibility.*;
   import flash.desktop.*;
   import flash.display.*;
   import flash.errors.*;
   import flash.events.*;
   import flash.external.*;
   import flash.filters.*;
   import flash.geom.*;
   import flash.globalization.*;
   import flash.media.*;
   import flash.net.*;
   import flash.net.drm.*;
   import flash.printing.*;
   import flash.profiler.*;
   import flash.sampler.*;
   import flash.sensors.*;
   import flash.system.*;
   import flash.text.*;
   import flash.text.engine.*;
   import flash.text.ime.*;
   import flash.ui.*;
   import flash.utils.*;
   import flash.xml.*;
   
   [Embed(source="/_assets/assets.swf", symbol="symbol2643")]
   public dynamic class a_Room_GuildHall extends MovieClip
   {
      
      public var am_Foreground_1:MovieClip;
      
      public var am_Midground_5:a_Scaffolding_Barn;
      
      public var am_CollisionObject:MovieClip;
      
      public var __id6_:ac_CraftBarn;
      
      public var am_DoorLocal_T:a_DoorLocal_T;
      
      public var __id8_:ac_NPCHomeWarden;
      
      public var __id9_:ac_NPCHomeRunecrafter;
      
      public function a_Room_GuildHall()
      {
         super();
         this.__setProp___id6__a_Room_GuildHall_Ground_0();
         this.__setProp___id8__a_Room_GuildHall_Cues_0();
         this.__setProp___id9__a_Room_GuildHall_Cues_0();
      }
      
      internal function __setProp___id6__a_Room_GuildHall_Ground_0() : *
      {
         try
         {
            this.__id6_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id6_.characterName = "Special_Barn";
         this.__id6_.displayName = "Hidden";
         this.__id6_.dramaAnim = "";
         this.__id6_.itemDrop = "";
         this.__id6_.sayOnActivate = "";
         this.__id6_.sayOnAlert = "";
         this.__id6_.sayOnBloodied = "";
         this.__id6_.sayOnDeath = "";
         this.__id6_.sayOnInteract = "Nothing";
         this.__id6_.sayOnSpawn = "";
         this.__id6_.sleepAnim = "";
         this.__id6_.team = "neutral";
         this.__id6_.waitToAggro = 0;
         try
         {
            this.__id6_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp___id8__a_Room_GuildHall_Cues_0() : *
      {
         try
         {
            this.__id8_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id8_.characterName = "Special_Falconer";
         this.__id8_.displayName = "Hidden";
         this.__id8_.dramaAnim = "";
         this.__id8_.itemDrop = "";
         this.__id8_.sayOnActivate = "";
         this.__id8_.sayOnAlert = "";
         this.__id8_.sayOnBloodied = "";
         this.__id8_.sayOnDeath = "";
         this.__id8_.sayOnInteract = "Please hatch more eggs, friend. Yval here might like a bit more company.";
         this.__id8_.sayOnSpawn = "";
         this.__id8_.sleepAnim = "";
         this.__id8_.team = "neutral";
         this.__id8_.waitToAggro = 0;
         try
         {
            this.__id8_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp___id9__a_Room_GuildHall_Cues_0() : *
      {
         try
         {
            this.__id9_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id9_.characterName = "Special_Guildmaster";
         this.__id9_.displayName = "Hidden";
         this.__id9_.dramaAnim = "";
         this.__id9_.itemDrop = "";
         this.__id9_.sayOnActivate = "";
         this.__id9_.sayOnAlert = "";
         this.__id9_.sayOnBloodied = "";
         this.__id9_.sayOnDeath = "";
         this.__id9_.sayOnInteract = "Welcome, warrior. Enjoy the Guild Hall.";
         this.__id9_.sayOnSpawn = "";
         this.__id9_.sleepAnim = "";
         this.__id9_.team = "neutral";
         this.__id9_.waitToAggro = 0;
         try
         {
            this.__id9_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
   }
}

