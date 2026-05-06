import pygame
import math
import random
from enum import Enum
from collections import deque
from datetime import datetime

# =============================================================================
# 상수 및 색상 정의
# =============================================================================

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# 색상
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (100, 100, 100)
COLOR_LIGHT_GRAY = (200, 200, 200)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_RED = (255, 0, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_MAGENTA = (255, 0, 255)
COLOR_ORANGE = (255, 165, 0)
COLOR_CYAN = (0, 255, 255)

# =============================================================================
# 차량 상태 Enum
# =============================================================================

class VehicleState(Enum):
    ENTERING = "입차"      # 입차 경로를 따라 이동
    PARKING = "주차"       # 주차 구역에서 대기
    WAITING = "대기"       # 출차 대기 지점에서 대기
    EXITING = "출차"       # 출차 경로를 따라 이동
    COMPLETED = "완료"     # 시스템 제거됨

# =============================================================================
# 경로 정의 (좌표 기반)
# =============================================================================

ENTRY_PATH = [
    (1150, 400),  # 시작점 (오른쪽 입구)
    (1050, 400),
    (950, 400),
    (850, 400),
    (750, 400),
    (650, 400),
    (550, 400),
    (450, 400),
    (350, 400),
    (250, 400),
    (150, 400),
    (150, 350),
    (150, 300),
    (150, 250),
    (150, 200),   # 주차 구역 앞 (왼쪽)
]

PARKING_AREA = [
    (50, 100),
    (250, 100),
    (250, 300),
    (50, 300)
]

# 출차 경로 (대기 지점 포함)
EXIT_PATH = [
    (150, 200),    # 주차 구역을 떠남
    (150, 150),
    (150, 100),
    (150, 50),
    (200, 50),
    (300, 50),
    (400, 50),
    (500, 50),
    (600, 50),
    (700, 50),
    (800, 50),
    (900, 50),
    (1000, 50),
    (1100, 50),
    (1200, 50),    # 출구
]

WAITING_POINT_INDEX = 3  # 대기 지점 (EXIT_PATH의 인덱스)
WAITING_POINT = EXIT_PATH[WAITING_POINT_INDEX]

# =============================================================================
# 차량 클래스
# =============================================================================

class Vehicle:
    vehicle_id_counter = 0
    
    def __init__(self, vehicle_type="A"):
        Vehicle.vehicle_id_counter += 1
        self.id = Vehicle.vehicle_id_counter
        self.vehicle_type = vehicle_type
        self.state = VehicleState.ENTERING
        self.path_index = 0
        self.x = ENTRY_PATH[0][0]
        self.y = ENTRY_PATH[0][1]
        
        # 주차 시간 (프레임 단위)
        if vehicle_type == "A":
            self.parking_duration = 300  # 약 5초 (60fps 기준)
        else:  # "B"
            self.parking_duration = 600  # 약 10초
        
        self.parking_time = 0
        self.radius = 8
        self.color = COLOR_GREEN
        self.is_reference_vehicle = False
    
    def update(self, allowing_exit=True):
        """차량 상태 업데이트"""
        if self.state == VehicleState.ENTERING:
            self._update_entering()
        elif self.state == VehicleState.PARKING:
            self._update_parking()
        elif self.state == VehicleState.WAITING:
            self._update_waiting(allowing_exit)
        elif self.state == VehicleState.EXITING:
            self._update_exiting()
    
    def _update_entering(self):
        """입차 상태 업데이트"""
        if self.path_index < len(ENTRY_PATH) - 1:
            self.path_index += 1
            self.x, self.y = ENTRY_PATH[self.path_index]
            self.color = COLOR_GREEN
        else:
            # 주차 구역에 도달
            self.state = VehicleState.PARKING
            self.parking_time = 0
            self.color = COLOR_BLUE
    
    def _update_parking(self):
        """주차 상태 업데이트"""
        self.parking_time += 1
        if self.parking_time >= self.parking_duration:
            # 주차 완료, 출차 대기로 전환
            self.state = VehicleState.WAITING
            self.path_index = 0
            self.color = COLOR_YELLOW
    
    def _update_waiting(self, allowing_exit):
        """대기 상태 업데이트"""
        if allowing_exit:
            # 출차 시작
            self.state = VehicleState.EXITING
            self.path_index = WAITING_POINT_INDEX
            self.x, self.y = EXIT_PATH[self.path_index]
            self.color = COLOR_RED
    
    def _update_exiting(self):
        """출차 상태 업데이트"""
        if self.path_index < len(EXIT_PATH) - 1:
            self.path_index += 1
            self.x, self.y = EXIT_PATH[self.path_index]
            self.color = COLOR_RED
        else:
            # 출차 완료
            self.state = VehicleState.COMPLETED
    
    def is_at_waiting_point(self):
        """차량이 대기 지점에 있는지 확인"""
        if self.state == VehicleState.WAITING:
            wx, wy = WAITING_POINT
            if abs(self.x - wx) < 20 and abs(self.y - wy) < 20:
                return True
        return False
    
    def draw(self, surface):
        """화면에 차량 그리기"""
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        
        # 기준 차량이면 테두리 그리기
        if self.is_reference_vehicle:
            pygame.draw.circle(surface, COLOR_MAGENTA, (int(self.x), int(self.y)), 
                             self.radius + 3, 2)

# =============================================================================
# 교통 관리 시스템 클래스
# =============================================================================

class TrafficManagementSystem:
    def __init__(self):
        self.vehicles = []
        self.generation_interval = 30  # 프레임 단위
        self.generation_counter = 0
        self.frame_count = 0
        
        # 교통 제어 매개변수
        self.max_waiting_vehicles = 3  # 대기 차량 최대 기준
        self.allowing_entry = True
        self.reference_vehicle = None
        
        # 통계
        self.total_generated = 0
        self.total_completed = 0
        self.cycle_count = 0
        
        # 상태 추적
        self.last_state = None
    
    def update(self):
        """시스템 업데이트"""
        self.frame_count += 1
        
        # 차량 생성
        if self.allowing_entry:
            self.generation_counter += 1
            if self.generation_counter >= self.generation_interval:
                self._generate_vehicle()
                self.generation_counter = 0
        
        # 대기 차량 수 확인
        waiting_count = self._count_waiting_vehicles()
        
        # 교통 제어 로직
        self._control_traffic(waiting_count)
        
        # 차량 업데이트
        vehicles_to_remove = []
        for vehicle in self.vehicles:
            allowing_exit = not self.allowing_entry or \
                          (self.reference_vehicle and \
                           self.reference_vehicle.state == VehicleState.PARKING)
            
            vehicle.update(allowing_exit)
            
            if vehicle.state == VehicleState.COMPLETED:
                vehicles_to_remove.append(vehicle)
                self.total_completed += 1
        
        # 완료된 차량 제거
        for vehicle in vehicles_to_remove:
            self.vehicles.remove(vehicle)
        
        # 모든 차량이 완료되었을 때 다시 입차 허용
        if not self.vehicles and not self.allowing_entry:
            self.allowing_entry = True
            self.reference_vehicle = None
            self.cycle_count += 1
    
    def _generate_vehicle(self):
        """차량 생성"""
        vehicle_type = random.choice(["A", "B"])
        vehicle = Vehicle(vehicle_type)
        self.vehicles.append(vehicle)
        self.total_generated += 1
    
    def _count_waiting_vehicles(self):
        """대기 지점에서 대기 중인 차량 수 계산"""
        count = 0
        for vehicle in self.vehicles:
            if vehicle.state == VehicleState.WAITING:
                count += 1
        return count
    
    def _control_traffic(self, waiting_count):
        """교통 흐름 제어"""
        if self.allowing_entry:
            if waiting_count >= self.max_waiting_vehicles:
                # 대기 차량이 충분하면 입차 중단
                self.allowing_entry = False
                # 마지막 입차 중인 차량을 기준 차량으로 설정
                for vehicle in reversed(self.vehicles):
                    if vehicle.state == VehicleState.ENTERING:
                        self.reference_vehicle = vehicle
                        vehicle.is_reference_vehicle = True
                        break
    
    def get_current_vehicle_count(self):
        """현재 시스템 내 차량 수"""
        return len(self.vehicles)
    
    def get_waiting_vehicle_count(self):
        """현재 대기 중인 차량 수"""
        return self._count_waiting_vehicles()
    
    def draw_infrastructure(self, surface):
        """도로, 주차구역 등 인프라 그리기"""
        # 입차 경로
        for i in range(len(ENTRY_PATH) - 1):
            pygame.draw.line(surface, COLOR_CYAN, ENTRY_PATH[i], ENTRY_PATH[i+1], 2)
        
        # 주차 구역
        pygame.draw.polygon(surface, COLOR_LIGHT_GRAY, PARKING_AREA, 1)
        font = pygame.font.Font(None, 20)
        text = font.render("PARKING", True, COLOR_GRAY)
        surface.blit(text, (80, 180))
        
        # 출차 경로
        for i in range(len(EXIT_PATH) - 1):
            pygame.draw.line(surface, COLOR_CYAN, EXIT_PATH[i], EXIT_PATH[i+1], 2)
        
        # 대기 지점
        pygame.draw.circle(surface, COLOR_ORANGE, WAITING_POINT, 6)
        
        # 도로 레이블
        font = pygame.font.Font(None, 18)
        entry_text = font.render("ENTRY", True, COLOR_CYAN)
        surface.blit(entry_text, (600, 420))
        
        exit_text = font.render("EXIT", True, COLOR_CYAN)
        surface.blit(exit_text, (600, 30))
    
    def draw_vehicles(self, surface):
        """모든 차량 그리기"""
        for vehicle in self.vehicles:
            vehicle.draw(surface)
    
    def draw_info_panel(self, surface):
        """정보 패널 그리기 (좌상단)"""
        font_title = pygame.font.Font(None, 18)
        font_info = pygame.font.Font(None, 16)
        
        info_texts = [
            f"[시스템 정보]",
            f"생성된 차량: {self.total_generated}",
            f"완료된 차량: {self.total_completed}",
            f"현재 시스템 내: {self.get_current_vehicle_count()}",
            f"대기 중인 차량: {self.get_waiting_vehicle_count()}",
            f"완료된 주기: {self.cycle_count}",
            f"입차 허용: {'YES' if self.allowing_entry else 'NO'}",
            f"기준 차량: {self.reference_vehicle.id if self.reference_vehicle else 'None'}",
        ]
        
        y_offset = 10
        for i, text in enumerate(info_texts):
            if i == 0:
                rendered_text = font_title.render(text, True, COLOR_WHITE)
            else:
                rendered_text = font_info.render(text, True, COLOR_WHITE)
            surface.blit(rendered_text, (10, y_offset))
            y_offset += 22
    
    def draw_legend(self, surface):
        """범례 그리기 (우하단)"""
        font = pygame.font.Font(None, 14)
        
        legend_items = [
            (COLOR_GREEN, "입차"),
            (COLOR_BLUE, "주차"),
            (COLOR_YELLOW, "대기"),
            (COLOR_RED, "출차"),
            (COLOR_ORANGE, "대기지점"),
        ]
        
        start_x = SCREEN_WIDTH - 150
        start_y = SCREEN_HEIGHT - 130
        
        title = font.render("[범례]", True, COLOR_WHITE)
        surface.blit(title, (start_x, start_y))
        
        for i, (color, label) in enumerate(legend_items):
            y = start_y + 25 + (i * 20)
            pygame.draw.circle(surface, color, (start_x + 10, y), 5)
            text = font.render(label, True, COLOR_WHITE)
            surface.blit(text, (start_x + 25, y - 7))

# =============================================================================
# 메인 애플리케이션
# =============================================================================

class Application:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("학교 교통 시뮬레이션 시스템")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.system = TrafficManagementSystem()
    
    def handle_events(self):
        """이벤트 처리"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def update(self):
        """업데이트"""
        self.system.update()
    
    def draw(self):
        """렌더링"""
        self.screen.fill(COLOR_BLACK)
        
        # 배경 (도로)
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # 인프라 그리기
        self.system.draw_infrastructure(self.screen)
        
        # 차량 그리기
        self.system.draw_vehicles(self.screen)
        
        # 정보 패널
        self.system.draw_info_panel(self.screen)
        
        # 범례
        self.system.draw_legend(self.screen)
        
        pygame.display.flip()
    
    def run(self):
        """메인 루프"""
        print("=" * 70)
        print("학교 교통 시뮬레이션 시스템 시작")
        print("=" * 70)
        print(f"화면 크기: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        print(f"FPS: {FPS}")
        print("종료: ESC 키 또는 창 닫기")
        print("=" * 70)
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        print("\n시뮬레이션 종료")
        print(f"총 생성 차량: {self.system.total_generated}")
        print(f"총 출차 완료: {self.system.total_completed}")
        print(f"완료된 주기: {self.system.cycle_count}")

# =============================================================================
# 프로그램 실행
# =============================================================================

if __name__ == "__main__":
    app = Application()
    app.run()
