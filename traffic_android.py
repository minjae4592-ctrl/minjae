"""
교통 관리 시뮬레이션 - Pydroid 3 안드로이드 버전
안드로이드 태블릿에 최적화된 버전
"""

import pygame
import math
import random
from enum import Enum
import os

# =============================================================================
# Pydroid 3 설정
# =============================================================================

# 안드로이드 화면 크기 (태블릿 최적화)
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

# 디바이스 성능 최적화
FPS = 30  # 배터리 효율을 위해 30fps로 설정
pygame.init()

# =============================================================================
# 상수 및 색상 정의
# =============================================================================

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
COLOR_DARK_BLUE = (0, 0, 100)

# =============================================================================
# 차량 상태 Enum
# =============================================================================

class VehicleState(Enum):
    ENTERING = "입차"
    PARKING = "주차"
    WAITING = "대기"
    EXITING = "출차"
    COMPLETED = "완료"

# =============================================================================
# 경로 정의 (안드로이드 화면에 맞춤)
# =============================================================================

ENTRY_PATH = [
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
    (150, 200),
]

PARKING_AREA = [
    (50, 100),
    (250, 100),
    (250, 300),
    (50, 300)
]

EXIT_PATH = [
    (150, 200),
    (150, 150),
    (150, 100),
    (150, 50),
    (250, 50),
    (350, 50),
    (450, 50),
    (550, 50),
    (650, 50),
    (750, 50),
    (850, 50),
    (950, 50),
    (1024, 50),
]

WAITING_POINT_INDEX = 3
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
        
        # 주차 시간 (프레임 단위, 30fps 기준)
        if vehicle_type == "A":
            self.parking_duration = 150  # 약 5초
        else:
            self.parking_duration = 300  # 약 10초
        
        self.parking_time = 0
        self.radius = 6
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
        if self.path_index < len(ENTRY_PATH) - 1:
            self.path_index += 1
            self.x, self.y = ENTRY_PATH[self.path_index]
            self.color = COLOR_GREEN
        else:
            self.state = VehicleState.PARKING
            self.parking_time = 0
            self.color = COLOR_BLUE
    
    def _update_parking(self):
        self.parking_time += 1
        if self.parking_time >= self.parking_duration:
            self.state = VehicleState.WAITING
            self.path_index = 0
            self.color = COLOR_YELLOW
    
    def _update_waiting(self, allowing_exit):
        if allowing_exit:
            self.state = VehicleState.EXITING
            self.path_index = WAITING_POINT_INDEX
            self.x, self.y = EXIT_PATH[self.path_index]
            self.color = COLOR_RED
    
    def _update_exiting(self):
        if self.path_index < len(EXIT_PATH) - 1:
            self.path_index += 1
            self.x, self.y = EXIT_PATH[self.path_index]
            self.color = COLOR_RED
        else:
            self.state = VehicleState.COMPLETED
    
    def draw(self, surface):
        """화면에 차량 그리기"""
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        
        if self.is_reference_vehicle:
            pygame.draw.circle(surface, COLOR_MAGENTA, (int(self.x), int(self.y)), 
                             self.radius + 2, 2)

# =============================================================================
# 교통 관리 시스템
# =============================================================================

class TrafficManagementSystem:
    def __init__(self):
        self.vehicles = []
        self.generation_interval = 20  # 프레임 단위
        self.generation_counter = 0
        self.frame_count = 0
        
        self.max_waiting_vehicles = 3
        self.allowing_entry = True
        self.reference_vehicle = None
        
        self.total_generated = 0
        self.total_completed = 0
        self.cycle_count = 0
    
    def update(self):
        """시스템 업데이트"""
        self.frame_count += 1
        
        if self.allowing_entry:
            self.generation_counter += 1
            if self.generation_counter >= self.generation_interval:
                self._generate_vehicle()
                self.generation_counter = 0
        
        waiting_count = self._count_waiting_vehicles()
        self._control_traffic(waiting_count)
        
        vehicles_to_remove = []
        for vehicle in self.vehicles:
            allowing_exit = not self.allowing_entry or \
                          (self.reference_vehicle and \
                           self.reference_vehicle.state == VehicleState.PARKING)
            
            vehicle.update(allowing_exit)
            
            if vehicle.state == VehicleState.COMPLETED:
                vehicles_to_remove.append(vehicle)
                self.total_completed += 1
        
        for vehicle in vehicles_to_remove:
            self.vehicles.remove(vehicle)
        
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
        """대기 차량 수"""
        count = 0
        for vehicle in self.vehicles:
            if vehicle.state == VehicleState.WAITING:
                count += 1
        return count
    
    def _control_traffic(self, waiting_count):
        """교통 제어"""
        if self.allowing_entry:
            if waiting_count >= self.max_waiting_vehicles:
                self.allowing_entry = False
                for vehicle in reversed(self.vehicles):
                    if vehicle.state == VehicleState.ENTERING:
                        self.reference_vehicle = vehicle
                        vehicle.is_reference_vehicle = True
                        break
    
    def get_current_vehicle_count(self):
        return len(self.vehicles)
    
    def get_waiting_vehicle_count(self):
        return self._count_waiting_vehicles()
    
    def draw_infrastructure(self, surface):
        """도로 및 시설 그리기"""
        # 입차 경로
        for i in range(len(ENTRY_PATH) - 1):
            pygame.draw.line(surface, COLOR_CYAN, ENTRY_PATH[i], ENTRY_PATH[i+1], 2)
        
        # 주차 구역
        pygame.draw.polygon(surface, COLOR_LIGHT_GRAY, PARKING_AREA, 1)
        font = pygame.font.Font(None, 16)
        text = font.render("P", True, COLOR_GRAY)
        surface.blit(text, (130, 190))
        
        # 출차 경로
        for i in range(len(EXIT_PATH) - 1):
            pygame.draw.line(surface, COLOR_CYAN, EXIT_PATH[i], EXIT_PATH[i+1], 2)
        
        # 대기 지점
        pygame.draw.circle(surface, COLOR_ORANGE, WAITING_POINT, 5)
    
    def draw_vehicles(self, surface):
        """차량 그리기"""
        for vehicle in self.vehicles:
            vehicle.draw(surface)
    
    def draw_info_panel(self, surface):
        """정보 패널 (안드로이드 최적화)"""
        font_title = pygame.font.Font(None, 16)
        font_info = pygame.font.Font(None, 14)
        
        info_texts = [
            f"[시스템 정보]",
            f"생성: {self.total_generated}",
            f"완료: {self.total_completed}",
            f"현재: {self.get_current_vehicle_count()}",
            f"대기: {self.get_waiting_vehicle_count()}",
            f"주기: {self.cycle_count}",
            f"입차: {'YES' if self.allowing_entry else 'NO'}",
            f"기준: {self.reference_vehicle.id if self.reference_vehicle else '-'}",
        ]
        
        y_offset = 5
        for i, text in enumerate(info_texts):
            if i == 0:
                rendered_text = font_title.render(text, True, COLOR_WHITE)
            else:
                rendered_text = font_info.render(text, True, COLOR_WHITE)
            surface.blit(rendered_text, (5, y_offset))
            y_offset += 18
    
    def draw_legend(self, surface):
        """범례 (우하단)"""
        font = pygame.font.Font(None, 12)
        
        legend_items = [
            (COLOR_GREEN, "입차"),
            (COLOR_BLUE, "주차"),
            (COLOR_YELLOW, "대기"),
            (COLOR_RED, "출차"),
        ]
        
        start_x = SCREEN_WIDTH - 120
        start_y = SCREEN_HEIGHT - 90
        
        for i, (color, label) in enumerate(legend_items):
            y = start_y + (i * 18)
            pygame.draw.circle(surface, color, (start_x + 8, y), 4)
            text = font.render(label, True, COLOR_WHITE)
            surface.blit(text, (start_x + 20, y - 6))

# =============================================================================
# 안드로이드 앱
# =============================================================================

class AndroidTrafficApp:
    def __init__(self):
        """안드로이드 앱 초기화"""
        # 안드로이드에서 전체 화면 사용
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Traffic Management System")
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.system = TrafficManagementSystem()
        
        # 터치 반응 시간 추적
        self.last_touch = 0
    
    def handle_events(self):
        """이벤트 처리"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                # 백 버튼 (ESC)
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                # 스페이스로 일시정지
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
            
            # 터치 이벤트 처리
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                self._handle_touch(x, y)
    
    def _handle_touch(self, x, y):
        """터치 입력 처리"""
        # 상단 일시정지 버튼 영역
        if x < 100 and y < 40:
            self.paused = not self.paused
    
    def update(self):
        """업데이트"""
        if not self.paused:
            self.system.update()
    
    def draw(self):
        """렌더링"""
        self.screen.fill(COLOR_DARK_BLUE)
        
        # 인프라
        self.system.draw_infrastructure(self.screen)
        
        # 차량
        self.system.draw_vehicles(self.screen)
        
        # 정보 패널
        self.system.draw_info_panel(self.screen)
        
        # 범례
        self.system.draw_legend(self.screen)
        
        # 일시정지 표시
        if self.paused:
            self._draw_pause_indicator()
        
        # 안드로이드 컨트롤 버튼
        self._draw_controls()
        
        pygame.display.flip()
    
    def _draw_pause_indicator(self):
        """일시정지 표시"""
        font = pygame.font.Font(None, 24)
        text = font.render("[PAUSED]", True, COLOR_YELLOW)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - 50, 10))
    
    def _draw_controls(self):
        """안드로이드 컨트롤 버튼"""
        font = pygame.font.Font(None, 12)
        
        # 일시정지 버튼 (좌상단)
        pause_text = "SPACE: PAUSE" if not self.paused else "SPACE: RESUME"
        text = font.render(pause_text, True, COLOR_CYAN)
        self.screen.blit(text, (5, 5))
        
        # 종료 안내 (우상단)
        exit_text = "ESC: EXIT"
        text = font.render(exit_text, True, COLOR_CYAN)
        self.screen.blit(text, (SCREEN_WIDTH - 80, 5))
    
    def run(self):
        """메인 루프"""
        print("=" * 70)
        print("Pydroid 3 - 학교 교통 관리 시뮬레이션")
        print("=" * 70)
        print(f"화면 크기: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        print(f"FPS: {FPS} (배터리 효율 모드)")
        print(f"조작:")
        print(f"  - SPACE 키: 일시정지/재개")
        print(f"  - ESC 키: 종료")
        print("=" * 70)
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        print("\n시뮬레이션 종료")
        print(f"총 생성: {self.system.total_generated}")
        print(f"총 완료: {self.system.total_completed}")
        print(f"완료된 주기: {self.system.cycle_count}")

# =============================================================================
# 메인
# =============================================================================

if __name__ == "__main__":
    app = AndroidTrafficApp()
    app.run()
