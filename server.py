import math
import pickle
import socket
from random import randrange as rr
import sys
import pygame as pg
from numba import jit, prange

sc = pg.display.set_mode((4, 4))

# Инициализация сервера
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind(('127.0.0.1',50000))
socket.setblocking(0)
socket.listen(5)

# Классы
class Player:
	def __init__(self, socket, name, position, skin, angle, ready):
		self.socket = socket
		self.angle = angle
		self.angle_target = angle
		self.name = name
		self.pos = position
		self.skin = skin
		self.ready = ready
		self.disconnect = False
		self.errors = 0
		self.viewer = 'current'
		self.tails = []
		self.size = 35
		self.lenght = 1
		self.real_tails = []
		self.screen = [800, 450]
		self.scroll = self.pos
		self.target_size = self.size
		self.round_positions = 1
		self.left = 0
		self.right = 0
		self.bottom = 0
		self.top = 0
		self.ticks = 0
		self.start = 0
		self.data = {}
		

	def update(self):
		if not self.ready == 6:
			self.ticks += 1
			self.lenght = self.smooth_increase(self.lenght, self.target_size, 0.1, 2)
			if self.ticks % 5 == 0: self.snake_rect()
			self.angle = round(self.angle, 5)
			self.tails.insert(0, [round(self.pos[0], self.round_positions), round(self.pos[1], self.round_positions)])
			self.pos[0] = round(self.pos[0], self.round_positions); self.pos[1] = round(self.pos[1], self.round_positions)
			self.real_tails = self.tails[0 : int(self.lenght) : 3]

	def screen_size(self):
		self.screen_rect = pg.Rect(self.pos, self.screen)
		self.screen_rect.center = self.scroll
		return self.screen_rect

	def snake_rect(self):
		try:
			self.left = min(self.real_tails[i][0] for i in prange(len(self.real_tails))) - self.size/10
			self.right = max(self.real_tails[i][0] for i in prange(len(self.real_tails))) + self.size/10
			self.bottom = max(self.real_tails[i][1] for i in prange(len(self.real_tails))) +  self.size/10
			self.top = min(self.real_tails[i][1] for i in prange(len(self.real_tails))) - self.size/10
			data = [self.left, self.right, self.top, self.bottom]
			return data
		except Exception as e:
			return []

	def smooth_increase(self, value, value2, addition, fractions):
		if round(value2, fractions) > round(value, fractions):
			value += addition
		if round(value2, fractions) < round(value, fractions):
			value -= addition
		return value
	
	def smooth_increase_reverse(self, value, value2, addition, fractions):
		if round(value2, fractions) < round(value, fractions):
			value -= addition
		if round(value2, fractions) > round(value, fractions):
			value += addition
		return value

	def wall_collide_and_movement(self, delta_time, arena):
		if self.pos[0] < 0+self.size/10:
			return True
		elif self.pos[0] > 1000*arena-self.size/10:
			return True
		else:
			self.pos[0] += math.sin(self.angle)*2

		if self.pos[1] < 0+self.size/10:
			return True
		elif self.pos[1] > 1000*arena-self.size/10:
			return True
		else:
			self.pos[1] += math.cos(self.angle)*2

		return False
	def get_pos(self):
		return [round(self.pos[0], self.round_positions), round(self.pos[1], self.round_positions)]
	
	def optimization(self, data):
		sn = pg.Rect((0,0), (0,0))
		sn.x = data[0]; sn.y = data[2]; sn.size = (data[1] - data[0], data[3] - data[2])
		if self.screen_size().colliderect(sn):
			return True
		else: 
			return False
	def camera_controller(self, pos):
		scroll_x = self.scroll[0]
		scroll_y = self.scroll[1]
		if pos[0] - self.scroll[0] != 0:
			scroll_x += (pos[0]*self.scroll_z-self.scroll[0])/30
		
		if pos[1] - self.scroll[1] != 0:
			scroll_y += (pos[1]*self.scroll_z-self.scroll[1])/30
		
		self.scroll = [scroll_x, scroll_y]

	def collide_snake(self, snake):
		if math.sqrt(pow(snake.pos[0] - self.pos[0], 2) + pow(snake.pos[1] - self.pos[1], 2)) < (self.size/10 + snake.size/10):
			return True
		else:
			return False
	def collide_tail(self, snake):
		for i in range(len(snake.real_tails)):
			if math.sqrt(pow(self.pos[0] - snake.real_tails[i][0], 2) + pow(self.pos[1] - snake.real_tails[i][1], 2)) < (self.size/10 + snake.size/10):
				return True
		return False

class Bot(Player):
	def update_bot(self):
		if self.ticks % 70 == 0:
			self.angle_target = math.radians(rr(360))
		if self.ticks % 10 == 0:
			if self.pos[0] < 100:
				self.angle_target  = 1.5
			elif self.pos[0] > (arena*1000-100):
				self.angle_target = -1.5
			
			if self.pos[1] < 100:
				self.angle_target = 0
			elif self.pos[1] > (arena*1000-100):
				self.angle_target = -3.14

		self.angle = self.smooth_increase(self.angle, self.angle_target, 0.1, 3)

def generate_food(tails, incerate, intensity):
	a = []
	for i in range(int(len(tails)/intensity)):
		a.append(Food(tails[i][0] + (rr(incerate*2)-(incerate/2)), tails[i][1] + (rr(incerate*2)-(incerate/2)), food_r))
	return a

class Food:
	def __init__(self, x, y, r):
		self.x = x
		self.y = y
		self.r = r

	def collide_rect(self, rect):
		if self.x+self.r > rect.x and self.x-self.r < rect.right and self.y+self.r > rect.y and self.y-self.r < rect.bottom:
			return True
		else:
			return False
		
	def collide_snake(self, x, y, r):
		if math.sqrt(pow(x - self.x, 2) + pow(y - self.y, 2)) < (self.r + r):
			return True
		else:
			return False


# Переменные сервера
arena = 3 # x1000 pixels
clock = pg.time.Clock()
ticks = 0
players = []
food_amount = 800
recommendet_players = 14
food_r = 10
foods = [Food(rr(100, arena*1000 - 100), rr(100, arena*1000 - 100), food_r) for i in prange(food_amount)]

for i in range(recommendet_players):
	players.append(Bot('...', 'Bot ' + str(rr(10000)), [rr(100, arena*1000-100), rr(100, arena*1000-100)], rr(4), rr(6), 8))

while True:
	delta_time = clock.tick(100)
	ticks += 1
	for ev in pg.event.get():
		if ev.type == pg.QUIT:
			exit()
	pg.display.set_caption(str(clock.get_fps()))

	# Добавляем ботов если игроков меньше чем реккомендованое количество
	if len(players) < recommendet_players:
		players.append(Bot('...', 'Bot ' + str(rr(10000)), [rr(100, arena*1000-100), rr(100, arena*1000-100)], rr(4), rr(6), 8))
	# Принимаем запросы игроков на подключение
	if ticks == 100:
		ticks = 0
		try:
			new_socket, addres = socket.accept()
			new_socket.setblocking(0)
			players.append(Player(new_socket, '', [rr(100, arena*1000-100), rr(100, arena*1000-100)], 0, rr(6), 0))
		except: pass
	
	# Получчаем команды игроков
	zp = -1
	for i in prange(len(players)):
		try:
			if not players[i].ready == 8: # Если игрок не бот
				if players[i].ready == 0: # Если игрок только что подключился то получаем от него данные о скине и имени
					ds = pickle.loads(players[i].socket.recv(128))
					players[i].name = ds[0][:16]
					players[i].skin = ds[1]
					players[i].ready = 1

				if players[i].ready == 1 and pickle.loads(players[i].socket.recv(512)) == "#YES!": # После отправки проверки на готовность игрока он должен прислать ДА!
					players[i].ready = 7
					print('ready')

				if players[i].ready == 7: # Если игрок уже в готовом состоянии то получаем от него угол направления движения змейки
					data = pickle.loads(players[i].socket.recv(128))
					if data == 'disconnect': # Если игрок прислал запрос на отключение то удаляем его
						zp = i
					else:
						players[i].angle = math.radians(int(data)-180)
			else: # Если игрок оказался ботом то обновляем его
				players[i].update_bot()

		except: pass
		# После полученя данных удаляем игроков которые подали запрос на отключение
		if zp >= 0:
			del players[zp]
	if len(foods) < food_amount:
		foods.append(Food(rr(100, arena*1000 - 100), rr(100, arena*1000 - 100), food_r))
	# Обновляем сосотояние игроков
	for i in prange(len(players)):
		players[i].update()
	# Отправляем команды игрокам
	dep = -1
	for i in prange(len(players)):
		try:
			if players[i].ready == 1: # Если игрок еще не готов то спрашиваем у него о готовности
				players[i].socket.send(pickle.dumps('#READY?'))

			elif players[i].ready == 7 or players[i].ready == 6 or players[i].ready == 8: # Если игрок живой - 7, если игрок НЕ живой - 6, если бот - 8
				dt = {'players': {}, 'info': {}, 'food': {}}
				if players[i].wall_collide_and_movement(delta_time, arena) and players[i].ready == 7: # Если игрок/бот(далее просо игрок) соприкасаеься с стеной, то он НЕ живой, а иначе двигается
					players[i].ready = 6
					foods.extend(generate_food(players[i].real_tails, 10, 5))

				for j in prange(len(players)): # Собираем в словарь всех игроков которых видит игрок, и проверяем с ними коллизии
					if players[i].optimization(players[j].snake_rect()):
						dt['players'].update({j: {'pos': players[j].get_pos(), 'name': players[j].name, 'angle': players[j].angle, 'tail': players[j].real_tails, 'size': players[j].size, 'ready': players[j].ready, 'skin': players[j].skin}})
						if not players[i] == players[j]: # Если текущий игрок i НЕ == текущему игроку j 
							if players[i].collide_snake(players[j]) and not players[j].ready == 6 and not players[i].ready == 6:
								if players[i].size > players[j].size:
									players[i].ready = 6
									players[i].viewer = j
									foods.extend(generate_food(players[i].real_tails, 10, 5))
								else:
									foods.extend(generate_food(players[j].real_tails, 10, 5))
									players[j].ready = 6
							if players[i].collide_tail(players[j]) and not players[j].ready == 6 and not players[i].ready == 6: # Если игрок столкнулся с хвостом другого игрока
								players[i].ready = 6
								players[i].viewer = j
								foods.extend(generate_food(players[i].real_tails, 10, 5)) # Добавляем еду в мир при столкновении змейки
				de = -1
				f = []
				if players[i].ticks % 10 == 0: # С частотой 10 фреймов отправляем еду
					for g in prange(len(foods)):
						if foods[g].collide_rect(players[i].screen_size()):
							f.append([foods[g].x, foods[g].y])
							if foods[g].collide_snake(players[i].pos[0], players[i].pos[1], players[i].size/10):
								players[i].target_size += 1
								de = g
					dt['food'].update({'f': f})
				if not de == -1:
					foods.remove(foods[de])


					
				if players[i].ticks % 10 == 0: # С частотой 10 фреймов отправляем информацию о мире
					dt['info'].update({'viewer': i if players[i].viewer == 'current' else players[i].viewer, 'size': arena, 'players': len(players), 'food_r': food_r})
				if not players[i].ready == 8: # Если игрок НЕ бот, то отправляем данные
					players[i].socket.send(pickle.dumps(dt))

				if players[i].disconnect: # Если игрок отключился то отключаем
					players[i].socket.send(pickle.dumps('disconnect'))

				if players[i].ready == 6:
					players[i].errors += 1

				else:
					players[i].errors = 0
		except:
			players[i].errors += 1

		if players[i].errors > 490:
			players[i].disconnect = True

		if players[i].errors > 500:
			if not players[i].socket == '...': # Если игрок не бот
				try:
					players[i].socket.send(pickle.dumps('disconnect'))
				except: pass
				dep = i

	if dep >= 0: # Отключаем игроков
		del players[dep]
