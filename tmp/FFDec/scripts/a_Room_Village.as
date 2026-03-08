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
   
   [Embed(source="/_assets/assets.swf", symbol="symbol2595")]
   public dynamic class a_Room_Village extends MovieClip
   {
      public var __id11_:ac_NPCHomeGemMerchant;
      
      public var am_Foreground_2:MovieClip;
      
      public var am_SwappableDyer:MovieClip;
      
      public var __id14_:ac_GenericEnt;
      
      public var __id15_:ac_GenericEnt;
      
      public var am_CollisionObject:MovieClip;
      
      public var am_SwappableSmithy:MovieClip;
      
      public var __id12_:ac_NPCHomeAlchemist;
      
      public var am_MaterialVendor:MovieClip;
      
      public var __id13_:ac_NPCHomeInnkeeper;
      
      public function a_Room_Village()
      {
         super();
         this.__setProp___id11__a_Room_Village_Cues_0();
         this.__setProp___id12__a_Room_Village_Cues_0();
         this.__setProp___id13__a_Room_Village_Cues_0();
         this.__setProp___id14__a_Room_Village_Cues_0();
         this.__setProp___id15__a_Room_Village_Cues_0();
      }
      
      internal function __setProp___id11__a_Room_Village_Cues_0() : *
      {
         try
         {
            this.__id11_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id11_.characterName = "Special_RoyalSigil";
         this.__id11_.displayName = "Hidden";
         this.__id11_.dramaAnim = "";
         this.__id11_.itemDrop = "";
         this.__id11_.sayOnActivate = "";
         this.__id11_.sayOnAlert = "";
         this.__id11_.sayOnBloodied = "";
         this.__id11_.sayOnDeath = "";
         this.__id11_.sayOnInteract = "Come back later and I\'ll tell you how to open these chests!=They have all kinds of treasure inside!=I also might sell you some of what I\'ve got in my bag.=Don\'t forget!";
         this.__id11_.sayOnSpawn = "";
         this.__id11_.sleepAnim = "";
         this.__id11_.team = "neutral";
         this.__id11_.waitToAggro = 0;
         try
         {
            this.__id11_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp___id12__a_Room_Village_Cues_0() : *
      {
         try
         {
            this.__id12_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id12_.characterName = "Special_Dyer";
         this.__id12_.displayName = "Hidden";
         this.__id12_.dramaAnim = "";
         this.__id12_.itemDrop = "";
         this.__id12_.sayOnActivate = "";
         this.__id12_.sayOnAlert = "";
         this.__id12_.sayOnBloodied = "";
         this.__id12_.sayOnDeath = "";
         this.__id12_.sayOnInteract = "Nothing";
         this.__id12_.sayOnSpawn = "";
         this.__id12_.sleepAnim = "";
         this.__id12_.team = "neutral";
         this.__id12_.waitToAggro = 0;
         try
         {
            this.__id12_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp___id13__a_Room_Village_Cues_0() : *
      {
         try
         {
            this.__id13_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id13_.characterName = "Special_Innkeeper";
         this.__id13_.displayName = "Hidden";
         this.__id13_.dramaAnim = "";
         this.__id13_.itemDrop = "";
         this.__id13_.sayOnActivate = "";
         this.__id13_.sayOnAlert = "";
         this.__id13_.sayOnBloodied = "";
         this.__id13_.sayOnDeath = "";
         this.__id13_.sayOnInteract = "This is your place now.=This place has been overrun since the goblins came.=But I bet you can set things right.=That old forge once forged powerful magic items.=It could again.=The tome trained the most powerful heroes of the last age.=But that was then.=I can remember how great this place was once.=There was a fountain of tremendous magic.=And forests full of wild magical animals.=This place could be great again.=This village could thrive again.=If only a hero could lead the way.=Yep.";
         this.__id13_.sayOnSpawn = "";
         this.__id13_.sleepAnim = "";
         this.__id13_.team = "neutral";
         this.__id13_.waitToAggro = 0;
         try
         {
            this.__id13_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp___id14__a_Room_Village_Cues_0() : *
      {
         try
         {
            this.__id14_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id14_.characterName = ",NPCTreasureTroveArt";
         this.__id14_.displayName = "";
         this.__id14_.dramaAnim = "";
         this.__id14_.itemDrop = "";
         this.__id14_.sayOnActivate = "";
         this.__id14_.sayOnAlert = "";
         this.__id14_.sayOnBloodied = "";
         this.__id14_.sayOnDeath = "";
         this.__id14_.sayOnInteract = "";
         this.__id14_.sayOnSpawn = "";
         this.__id14_.sleepAnim = "";
         this.__id14_.team = "neutral";
         this.__id14_.waitToAggro = 0;
         try
         {
            this.__id14_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp___id15__a_Room_Village_Cues_0() : *
      {
         try
         {
            this.__id15_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id15_.characterName = "Special_TreasureTrove,NPCTreasureTrove";
         this.__id15_.displayName = "Hidden";
         this.__id15_.dramaAnim = "";
         this.__id15_.itemDrop = "";
         this.__id15_.sayOnActivate = "";
         this.__id15_.sayOnAlert = "";
         this.__id15_.sayOnBloodied = "";
         this.__id15_.sayOnDeath = "";
         this.__id15_.sayOnInteract = "Nothing";
         this.__id15_.sayOnSpawn = "";
         this.__id15_.sleepAnim = "";
         this.__id15_.team = "neutral";
         this.__id15_.waitToAggro = 0;
         try
         {
            this.__id15_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
   }
}

