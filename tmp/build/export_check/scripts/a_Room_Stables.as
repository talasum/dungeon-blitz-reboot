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
   
   [Embed(source="/_assets/assets.swf", symbol="symbol2419")]
   public dynamic class a_Room_Stables extends MovieClip
   {
      
      public var am_CollisionObject:MovieClip;
      
      public var __id21_:ac_NPCHomeStablemaster;
      
      public function a_Room_Stables()
      {
         super();
         this.__setProp___id21__a_Room_Stables_Road_0();
      }
      
      internal function __setProp___id21__a_Room_Stables_Road_0() : *
      {
         try
         {
            this.__id21_["componentInspectorSetting"] = true;
         }
         catch(e:Error)
         {
         }
         this.__id21_.characterName = "Special_Stablemaster";
         this.__id21_.displayName = "Hidden";
         this.__id21_.dramaAnim = "";
         this.__id21_.itemDrop = "";
         this.__id21_.sayOnActivate = "";
         this.__id21_.sayOnAlert = "";
         this.__id21_.sayOnBloodied = "";
         this.__id21_.sayOnDeath = "";
         this.__id21_.sayOnInteract = "My job is to look after these fine creatures.";
         this.__id21_.sayOnSpawn = "";
         this.__id21_.sleepAnim = "";
         this.__id21_.team = "neutral";
         this.__id21_.waitToAggro = 0;
         try
         {
            this.__id21_["componentInspectorSetting"] = false;
         }
         catch(e:Error)
         {
         }
      }
   }
}

