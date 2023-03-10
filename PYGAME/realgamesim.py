from pathlib import Path
import sys
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))
import pygame as pg
import random
from numpy import array,float32
import numpy as np
import lineintersectionutil
import player_AI
from lineintersectionutil import normalize
from collections import OrderedDict
from raycasting import *
pg.display.init()
pg.font.init()
SCREEN_WIDTH,SCREEN_HEIGHT=800,600
INVINCIBILITY_PERIOD = 1000
PLAYER_COLOR = (255,255,0)
PARTICLE_COLOR = (255,0,0)
screen = pg.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))




class Particle:
  def __init__(self, coord, rad,velocity=[0,0],bounce=False):
    x,y=coord
    self.x = x
    self.y = y
    self.rad = rad
    self.colour = PARTICLE_COLOR
    self.thickness = 1
    self.velocity = velocity
    self.bounce=bounce
    self.rect=None

  def draw(self,display_trajectory=False):
    global screen
    self.rect=pg.draw.circle(screen, self.colour, (self.x, self.y), self.rad)
    if display_trajectory:
        wx,wy=pg.display.get_window_size()
        #TODO: COMPUTE THIS
        window_lines = [((0,0),(SCREEN_WIDTH,0)),
                        ((SCREEN_WIDTH,0),(SCREEN_WIDTH,SCREEN_HEIGHT)),
                        ((SCREEN_WIDTH,SCREEN_HEIGHT),(0,SCREEN_HEIGHT)),
                        ((0,SCREEN_HEIGHT),(0,0))]
        dist=10*(SCREEN_WIDTH+SCREEN_HEIGHT)
        nx,ny = normalize(np.array(self.velocity))
        my_line = (
            (self.x,self.y),(self.x+dist*(nx),self.y+dist*(ny))
            )
        for wl in window_lines:
            ip= lineintersectionutil.lineLineIntersect(*wl,*my_line) 
            if ip is not None:
                pg.draw.line(screen,(255,255,255),(self.x,self.y),ip)
                return


        #end_pos = (0,0)
       # pg.draw.line(screen, (0,255,0), (self.x,self.y), end_pos)



  def update_position(self,dt):
      self.x+=self.velocity[0]*dt
      self.y+=self.velocity[1]*dt
      if self.bounce:
          if self.x>SCREEN_WIDTH:
              self.x=SCREEN_WIDTH
              self.velocity[0]*=-1
          if self.x<0:
              self.x=0
              self.velocity[0]*=-1

          if self.y>SCREEN_HEIGHT:
              self.y=SCREEN_HEIGHT
              self.velocity[1]*=-1
          if self.y<0:
              self.y=0
              self.velocity[1]*=-1
      
class Player:
  def __init__(self, coord, rad,speed=5,colour=PLAYER_COLOR,AI=False,screen=None,game=None):
    x,y=coord
    self.x = x
    self.y = y
    self.rad = rad
    self.colour = colour
    self.thickness = 1
    self.speed = speed
    self.velocity=[0,0]
    self.AI=AI
    self.health=1
    #is above 0 if player is invincible
    self.invincible_timer=0
    self.dodge_roll_dist=100
    self.dodge_roll_speed=0.8
    #is [0,0] if the player is NOT dodgerolling
    self.dodge_roll_dir=[0,0]
    #above 0 if the player is dodgerolling
    self.dodge_roll_timer=0
    self.rect=None
    self.game=game
    

    

  def draw(self,display_trajectory=False):
    global screen
    self.rect = pg.draw.circle(screen, self.colour, (self.x, self.y), self.rad)
    

 
  def cast_rays(self):
      distances=[]
      for i in range(20):
        angle = 2*np.pi/(20) *i
        dir = np.cos(angle),np.sin(angle)
        r=Ray([self.x,self.y],dir,500)
        rect,dist = r.cast(10,screen,self.game.parts)
        distances.append(dist)
      return distances
    
  def get_dir(self):
        keys = pg.key.get_pressed()  #checking pressed keys
        velocity=np.array([0,0])
        if keys[pg.K_LEFT]:
            velocity = np.add(velocity, (np.array([-1,0])))
            
        if keys[pg.K_RIGHT]:
            velocity =  np.add(velocity,(np.array([1,0])))

        if keys[pg.K_UP]:
            velocity = np.add(velocity,(np.array([0,-1])))
        if keys[pg.K_DOWN]:
            velocity = np.add(velocity,(np.array([0,1])))
        return normalize(velocity)


      
  def set_velocity(self,best_action:list = None):
        if self.dodge_roll_dir!=[0,0]:
            self.velocity = normalize(self.dodge_roll_dir)*self.dodge_roll_speed
            return
        if self.AI:
            self.velocity = np.array(normalize(best_action))*self.speed
            return
        
        self.velocity = self.get_dir()*self.speed
        return
        keys = pg.key.get_pressed()  #checking pressed keys
        self.velocity=np.array([0,0])
        if keys[pg.K_LEFT]:
            self.velocity = np.add(self.velocity, normalize(np.array([-1,0]))*self.speed)
            
        if keys[pg.K_RIGHT]:
            self.velocity =  np.add(self.velocity,normalize(np.array([1,0]))*self.speed)

        if keys[pg.K_UP]:
            self.velocity = np.add(self.velocity,normalize(np.array([0,-1]))*self.speed)
        if keys[pg.K_DOWN]:
            self.velocity = np.add(self.velocity,normalize(np.array([0,1]))*self.speed)

      
  def update_position(self,dt):
       # self.set_velocity()
        
        self.x +=self.velocity[0]*dt
        self.y +=self.velocity[1]*dt
        if self.x<0:
            self.x=0
        if self.y<0:
            self.y=0
        if self.x>SCREEN_WIDTH:
            self.x=SCREEN_WIDTH
        if self.y>SCREEN_HEIGHT:
            self.y=SCREEN_HEIGHT
      
  def update_invincible(self,dt):
        self.invincible_timer -=dt
        self.invincible_timer=max(0,self.invincible_timer)
        if self.invincible_timer ==0:
            self.colour = PLAYER_COLOR
            

  def update_dodge_roll(self,dt):
      #d = s*t ---- t = d/s
     # dodge_roll_time = self.dodge_roll_dist/self.dodge_roll_speed
      prev_timer = self.dodge_roll_timer
      self.dodge_roll_timer -=dt
      self.dodge_roll_timer=max(0,self.dodge_roll_timer)
      if self.dodge_roll_timer>0:
            self.colour = (255,255,255)
      elif self.dodge_roll_timer==0 and prev_timer>0:
            self.colour=PLAYER_COLOR
            self.dodge_roll_dir=[0,0]
      
      
  def dodge_roll(self,dir:list):
      if self.dodge_roll_dir==[0,0]:
        self.dodge_roll_dir=dir
        self.dodge_roll_timer=self.dodge_roll_dist/self.dodge_roll_speed



class Game:
    def __init__(self,FPS=60,AI_control=False,num_particles=20,velocity_multiplier=1,player_rad=5) -> None:
        self.FPS=FPS
        #self.player=None
        #self.parts=None
        self.clock = pg.time.Clock()
        self.time_since_game_start=0
        self.running=True
        self.AI_control=AI_control
        
        self.player = Player(coord=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2),rad=player_rad,speed=0.1,colour=PLAYER_COLOR,AI=self.AI_control,game=self)
        self.parts=self.spawn_particles(num_particles,velocty_multiplier=velocity_multiplier,bounce=True,uniformY=True,velocity=None)
        self.screen =screen
    
    def check_collisions(self):
        part_indices = self.player.rect.collidelistall(self.parts)
        for index in part_indices:
            self.parts[index].colour = list(np.random.choice(range(256), size=3))
            #print("COLOR CHANGED")
        
        
    def render(self):
        pg.display.update()
        
    def spawn_particles(self,num,velocty_multiplier=1,bounce=False,velocity=None,uniformY=False):
        parts=[]
        
        def coord_gen():
            if uniformY:
                initial = [0,0]
                while True:
                    initial = [0,initial[1] + SCREEN_HEIGHT/num]
                    yield initial
                    
            else:
                while True:
                    yield [ random.randrange(0,SCREEN_WIDTH) ,   random.randrange(0,SCREEN_HEIGHT) ]
                    
        #THIS NEEDS TO BE HERE. DONT KNOW WHY          
        gen = coord_gen()
        
        for i in range(num):
            if velocity is None:
                particle_velocity=[velocty_multiplier*(random.random()-0.5),velocty_multiplier*(random.random()-0.5)]
            else:
                particle_velocity = velocity
                
            
            parts.append(
                Particle(
                coord=next(gen),
                rad=5,
                velocity= lineintersectionutil.scale_list(particle_velocity,velocty_multiplier),
                bounce=bounce
                )
                )
            

        return parts


    def reset(self):
        #self.start_game()
        #self.FPS=FPS
        #self.player=None
        #self.parts=None
        #self.clock = pg.time.Clock()
        self.__init__(FPS=60,AI_control=self.AI_control)
        
    def step(self,action = None):
                reward=1
        
        
                player = self.player
                parts=self.parts
                clock=self.clock
                FPS=self.FPS
                screen.fill((0,0,0))
                #TIME IN MILLISECONDS SINCE PREVIOUS CALL(FRAME)
                dt=clock.tick(FPS)
                self.time_since_game_start+=dt
                for event in pg.event.get():
                    if event.type==pg.QUIT:
                        self.running=False
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_SPACE:
                            dir = player.get_dir()
                            if lineintersectionutil.norm(dir)>0:
                                player.dodge_roll(list(dir))
                        elif event.key == pg.K_z:
                            self.AI_control= True if not self.AI_control else False
                            self.player.AI = True if not self.player.AI else False
                        
            
                model = player_AI.model(player,parts,rad=5)
                player_state = player_AI.state(player,parts)
                action_scores = {tuple(action): model.Q(player_state,action,dt,SCREEN_WIDTH,SCREEN_HEIGHT) for action in player_AI.ACTIONS}
                best_action = max(action_scores, key=action_scores.get)
                
                #print(f'OPTIMAL ACTION IS TO MOVE {best_action}')
                
                player.set_velocity(action)
                player.update_position(dt)
                player.update_invincible(dt)
                player.update_dodge_roll(dt)
                ray_dists=player.cast_rays()
                player.draw() 
                
                
                bullet_positions=[]
                bullet_velocities=[]
                vectors_to_bullets=[]
                bullet_distances=[]
                for p in parts:
                    p.update_position(dt)
                    p.draw(True)
                    dist_between_bullet_player=lineintersectionutil.norm([p.x-player.x,p.y-player.y])
                    if dist_between_bullet_player <200 and len(bullet_velocities)<20:
                       
                        bullet_velocities.append(array(p.velocity))
                        bullet_positions.append(array([p.x,p.y]))
                    #bullet_velocities.append(np.array(p.velocity))
                    #vectors_to_bullets.append(np.array([p.x-player.x,p.y-player.y]))
                    #reward -= dist_between_bullet_player
                    #HIT DETECTION
                    perp_dist,moving_towards_player,time_to_min_dist,part_on_target = lineintersectionutil.perp_dist_part_player(p,[player.x,player.y],player_rad=player.rad, draw=False,screen=screen)
                    if player.invincible_timer<=0 and lineintersectionutil.norm([p.x-player.x,p.y-player.y])<=1 +p.rad + player.rad:
                        
                        player.health-=1
                        reward-=1
                        player.invincible_timer=INVINCIBILITY_PERIOD
                        player.colour = (0,255,0)
                
                
                while len(bullet_velocities)<20:
                    bullet_velocities.append(np.array([0.0,0.0]))
                    bullet_positions.append(array([0.0,0.0]))
                #self.check_collisions()
                #DEBUG INFO
                lineintersectionutil.draw_text(f'AI CONTROL : {("YES" if player.AI else "NO")}',screen,(SCREEN_WIDTH/1.5,0))
                lineintersectionutil.draw_text(f'HEALTH : {player.health}',screen,(SCREEN_WIDTH/1.5,20))
                lineintersectionutil.draw_text(f'OPTIMAL ACTION : {best_action}',screen,(SCREEN_WIDTH/1.5,40))
                lineintersectionutil.draw_text(f'INVINCIBLE : {("YES" if player.invincible_timer>0 else "NO")}',screen,(SCREEN_WIDTH/1.5,60))
                lineintersectionutil.draw_text(f'INVINCIBLE TIMER : {player.invincible_timer}',screen,(SCREEN_WIDTH/1.5,80))

                #REWARD SHAPING
                dist_from_screen = lineintersectionutil.get_distance_from_screen_edge([player.x,player.y],SCREEN_WIDTH,SCREEN_HEIGHT,self.screen)
                lineintersectionutil.draw_text(f'MIN SCREEN DISTANCE : {dist_from_screen}',screen,(SCREEN_WIDTH/1.5,100))
                lineintersectionutil.draw_text(f'TIME SINCE GAME START : {self.time_since_game_start}',screen,(SCREEN_WIDTH/1.5,120))


                
                if dist_from_screen<50:
                    reward=-10000000000
                observation = 0
                terminated = player.health == 0
                truncated = bool((self.time_since_game_start>1000*60))
                #print(array(bullet_positions).shape,array(bullet_velocities).shape)
                observation=OrderedDict([('position', array([player.x ,  player.y], dtype=float32)),
                                         ('velocity',array(player.velocity,dtype=float32)),
                                         ('bullet_positions', array(bullet_positions,dtype=float32)),
                                         
                                         ('bullet_velocities',array(bullet_velocities,dtype=float32)),
                                         #('vectors_to_bullets',array(vectors_to_bullets)),
                                         #('bullet_distances',array(bullet_distances,dtype=float32)),
                                        
                                         ])
                lineintersectionutil.draw_text(f'REWARD : {reward}',screen,(SCREEN_WIDTH/1.5,140))
                lineintersectionutil.draw_text(f'FPS : {round(1000/dt)}',screen,(SCREEN_WIDTH/1.5,160))
                lineintersectionutil.draw_text(f'MIN_RAY_DIST : {np.min(array(ray_dists))}',screen,(SCREEN_WIDTH/1.5,180))


                return observation,reward,terminated,truncated
        
    
    def start_game(self):
    ######### G A M E #############
        #self.running=True
        #moved to init
        pass
         
       



if __name__=='__main__':
 
        game = Game(FPS=60,AI_control=False)
        game.start_game()
        while game.running:
            game.step()
            game.render()