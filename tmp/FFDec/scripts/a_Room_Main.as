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
   
   [Embed(source="/_assets/assets.swf", symbol="symbol2700")]
   public dynamic class a_Room_Main extends MovieClip
   {
      public var __id2_:ac_CraftForge;
      
      public var am_CollisionObject:MovieClip;
      
      public var __id3_:ac_NPCHomeMailbox;
      
      public var am_Midground1:a_Scaffolding_Tower;
      
      public var am_Midground2:a_Scaffolding_Forge;
      
      public var am_Midground3:a_Scaffolding_Tome;
      
      public var am_Midground4:a_Scaffolding_House;
      
      public var __id4_:ac_CraftTower;
      
      public var __id5_:ac_CraftTome;
      
      public function a_Room_Main()
      {
         super();
         this.__setProp___id2__a_Room_Main_Cues_0();
         this.__setProp___id3__a_Room_Main_Cues_0();
         this.__setProp___id4__a_Room_Main_Cues_0();
         this.__setProp___id5__a_Room_Main_Cues_0();
      }
      
      internal function __setProp___id2__a_Room_Main_Cues_0() : *
      {
         try
         {
            this.__id2_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id2_.characterName = "Special_CraftForge";
         this.__id2_.displayName = "Hidden";
         this.__id2_.dramaAnim = "";
         this.__id2_.itemDrop = "";
         this.__id2_.sayOnActivate = "";
         this.__id2_.sayOnAlert = "";
         this.__id2_.sayOnBloodied = "";
         this.__id2_.sayOnDeath = "";
         this.__id2_.sayOnInteract = "Nothing";
         this.__id2_.sayOnSpawn = "";
         this.__id2_.sleepAnim = "";
         this.__id2_.team = "neutral";
         this.__id2_.waitToAggro = 0;
         try
         {
            this.__id2_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp___id3__a_Room_Main_Cues_0() : *
      {
         try
         {
            this.__id3_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id3_.characterName = "Special_Mailbox";
         this.__id3_.displayName = "Hidden";
         this.__id3_.dramaAnim = "";
         this.__id3_.itemDrop = "";
         this.__id3_.sayOnActivate = "";
         this.__id3_.sayOnAlert = "";
         this.__id3_.sayOnBloodied = "";
         this.__id3_.sayOnDeath = "";
         this.__id3_.sayOnInteract = "Nothing";
         this.__id3_.sayOnSpawn = "";
         this.__id3_.sleepAnim = "";
         this.__id3_.team = "neutral";
         this.__id3_.waitToAggro = 0;
         try
         {
            this.__id3_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp___id4__a_Room_Main_Cues_0() : *
      {
         try
         {
            this.__id4_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id4_.characterName = "Special_ClassTower";
         this.__id4_.displayName = "Hidden";
         this.__id4_.dramaAnim = "";
         this.__id4_.itemDrop = "";
         this.__id4_.sayOnActivate = "";
         this.__id4_.sayOnAlert = "";
         this.__id4_.sayOnBloodied = "";
         this.__id4_.sayOnDeath = "";
         this.__id4_.sayOnInteract = "Nothing";
         this.__id4_.sayOnSpawn = "";
         this.__id4_.sleepAnim = "";
         this.__id4_.team = "neutral";
         this.__id4_.waitToAggro = 0;
         try
         {
            this.__id4_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp___id5__a_Room_Main_Cues_0() : *
      {
         try
         {
            this.__id5_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id5_.characterName = "Special_AbilityTome";
         this.__id5_.displayName = "Hidden";
         this.__id5_.dramaAnim = "";
         this.__id5_.itemDrop = "";
         this.__id5_.sayOnActivate = "";
         this.__id5_.sayOnAlert = "";
         this.__id5_.sayOnBloodied = "";
         this.__id5_.sayOnDeath = "";
         this.__id5_.sayOnInteract = "Nothing";
         this.__id5_.sayOnSpawn = "";
         this.__id5_.sleepAnim = "";
         this.__id5_.team = "neutral";
         this.__id5_.waitToAggro = 0;
         try
         {
            this.__id5_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
   }
}

