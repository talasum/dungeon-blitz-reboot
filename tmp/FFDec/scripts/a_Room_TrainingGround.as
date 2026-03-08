package
{
   import flash.display.MovieClip;
   
   [Embed(source="/_assets/assets.swf", symbol="symbol2343")]
   public dynamic class a_Room_TrainingGround extends MovieClip
   {
      public var am_CollisionObject:MovieClip;
      
      public var am_Dummy3:ac_HomeDummy3;
      
      public var am_Dummy2:ac_HomeDummy2;
      
      public var am_Dummy1:ac_HomeDummy1;
      
      public var am_Parallax_3_2:MovieClip;
      
      public function a_Room_TrainingGround()
      {
         super();
         addFrameScript(0,this.frame1);
      }
      
      public function InitRoom(param1:a_GameHook) : void
      {
         param1.initialPhase = this.Tick;
      }
      
      public function Tick(param1:a_GameHook) : void
      {
         if(param1.AtTime(0))
         {
         }
      }
      
      internal function frame1() : *
      {
      }
   }
}

