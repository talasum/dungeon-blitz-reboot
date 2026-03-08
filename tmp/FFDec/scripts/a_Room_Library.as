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
   
   [Embed(source="/_assets/assets.swf", symbol="symbol2439")]
   public dynamic class a_Room_Library extends MovieClip
   {
      public var am_CollisionObject:MovieClip;
      
      public var __id19_:ac_NPCHomeXPBonus;
      
      public var __id20_:ac_NPCHomeFindingBonus;
      
      public function a_Room_Library()
      {
         super();
         this.__setProp___id19__a_Room_Library_Cues_0();
         this.__setProp___id20__a_Room_Library_Cues_0();
      }
      
      internal function __setProp___id19__a_Room_Library_Cues_0() : *
      {
         try
         {
            this.__id19_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id19_.characterName = "Special_XPBonus";
         this.__id19_.displayName = "Hidden";
         this.__id19_.dramaAnim = "";
         this.__id19_.itemDrop = "";
         this.__id19_.sayOnActivate = "";
         this.__id19_.sayOnAlert = "";
         this.__id19_.sayOnBloodied = "";
         this.__id19_.sayOnDeath = "";
         this.__id19_.sayOnInteract = "Nothing";
         this.__id19_.sayOnSpawn = "";
         this.__id19_.sleepAnim = "";
         this.__id19_.team = "neutral";
         this.__id19_.waitToAggro = 0;
         try
         {
            this.__id19_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
      
      internal function __setProp___id20__a_Room_Library_Cues_0() : *
      {
         try
         {
            this.__id20_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id20_.characterName = "Special_FindingBonus";
         this.__id20_.displayName = "Hidden";
         this.__id20_.dramaAnim = "";
         this.__id20_.itemDrop = "";
         this.__id20_.sayOnActivate = "";
         this.__id20_.sayOnAlert = "";
         this.__id20_.sayOnBloodied = "";
         this.__id20_.sayOnDeath = "";
         this.__id20_.sayOnInteract = "Nothing";
         this.__id20_.sayOnSpawn = "";
         this.__id20_.sleepAnim = "";
         this.__id20_.team = "neutral";
         this.__id20_.waitToAggro = 0;
         try
         {
            this.__id20_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
   }
}

