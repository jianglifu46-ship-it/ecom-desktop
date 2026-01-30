"""
历史记录管理 - 撤销/重做功能
"""
from typing import List, Optional
from dataclasses import dataclass
import copy


@dataclass
class HistoryState:
    """历史状态"""
    action_name: str
    state_data: dict


class HistoryManager:
    """历史记录管理器"""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._history: List[HistoryState] = []
        self._current_index: int = -1
        self._is_recording: bool = True
    
    def push(self, action_name: str, state_data: dict):
        """记录新状态"""
        if not self._is_recording:
            return
        
        if self._current_index < len(self._history) - 1:
            self._history = self._history[:self._current_index + 1]
        
        state = HistoryState(
            action_name=action_name,
            state_data=copy.deepcopy(state_data)
        )
        
        self._history.append(state)
        self._current_index = len(self._history) - 1
        
        if len(self._history) > self.max_history:
            self._history.pop(0)
            self._current_index -= 1
    
    def undo(self) -> Optional[dict]:
        """撤销"""
        if self._current_index > 0:
            self._current_index -= 1
            return copy.deepcopy(self._history[self._current_index].state_data)
        return None
    
    def redo(self) -> Optional[dict]:
        """重做"""
        if self._current_index < len(self._history) - 1:
            self._current_index += 1
            return copy.deepcopy(self._history[self._current_index].state_data)
        return None
    
    def can_undo(self) -> bool:
        return self._current_index > 0
    
    def can_redo(self) -> bool:
        return self._current_index < len(self._history) - 1
    
    def get_undo_action(self) -> Optional[str]:
        if self._current_index > 0:
            return self._history[self._current_index].action_name
        return None
    
    def get_redo_action(self) -> Optional[str]:
        if self._current_index < len(self._history) - 1:
            return self._history[self._current_index + 1].action_name
        return None
    
    def clear(self):
        self._history.clear()
        self._current_index = -1
    
    def pause_recording(self):
        self._is_recording = False
    
    def resume_recording(self):
        self._is_recording = True


class CanvasHistoryManager:
    """画布历史记录管理器"""
    
    def __init__(self, canvas, max_history: int = 50):
        self.canvas = canvas
        self.history = HistoryManager(max_history)
        self.save_state("初始状态")
    
    def save_state(self, action_name: str):
        """保存当前画布状态"""
        state_data = self.canvas.to_dict()
        self.history.push(action_name, state_data)
    
    def undo(self) -> bool:
        """撤销"""
        state_data = self.history.undo()
        if state_data:
            self._restore_state(state_data)
            return True
        return False
    
    def redo(self) -> bool:
        """重做"""
        state_data = self.history.redo()
        if state_data:
            self._restore_state(state_data)
            return True
        return False
    
    def _restore_state(self, state_data: dict):
        """恢复画布状态"""
        from .layer import create_layer_from_dict
        from .canvas import Screen
        
        self.history.pause_recording()
        
        self.canvas.width = state_data.get('width', 750)
        self.canvas.height = state_data.get('height', 1000)
        self.canvas.background_color = state_data.get('background_color', '#FFFFFF')
        self.canvas.selected_layer_id = state_data.get('selected_layer_id')
        
        self.canvas.layers = []
        for layer_data in state_data.get('layers', []):
            layer = create_layer_from_dict(layer_data)
            self.canvas.layers.append(layer)
        
        self.canvas.screens = []
        for screen_data in state_data.get('screens', []):
            screen = Screen.from_dict(screen_data)
            self.canvas.screens.append(screen)
        
        self.history.resume_recording()
    
    def can_undo(self) -> bool:
        return self.history.can_undo()
    
    def can_redo(self) -> bool:
        return self.history.can_redo()
    
    def get_undo_action(self) -> Optional[str]:
        return self.history.get_undo_action()
    
    def get_redo_action(self) -> Optional[str]:
        return self.history.get_redo_action()
