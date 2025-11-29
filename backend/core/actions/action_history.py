import enum
from typing import Any

from pydantic import BaseModel


class ActionType(str, enum.Enum):
    ASK_QUESTION = "ask_question_to_user"
    GET_RESPONSE = "get_user_response"
    TASK_COMPLETED = "task_completed"


class Action(BaseModel):
    name: str
    reason: str


class ActionSuccessResult(BaseModel):
    outputs: Any
    success: str


class ErrorInfo(BaseModel):
    message: str
    exception: str


class ActionFailureResult(BaseModel):
    reason: str
    error: ErrorInfo


ActionResult = ActionSuccessResult | ActionFailureResult


class ActionInstance(BaseModel):
    action: Action
    result: ActionResult
    summary: str

    def __str__(self):
        executed_action = f"Executed action: {self.action.name}"
        result = f"Result: {self.result}"

        return f"{executed_action}\n{result}\n{self.summary}"


class ActionHistory(BaseModel):
    actionInstances: list[ActionInstance] = []
    index: int = 0

    def __getitem__(self, index):
        return self.actionInstances[index]

    def __len__(self):
        return len(self.actionInstances)

    def __bool__(self):
        return len(self.actionInstances) > 0

    @property
    def current_action(self):
        if self.index == 0:
            return None
        return self.actionInstances[self.index - 1]

    def register_action(self, action, reason):
        ActionVal = Action(name=action, reason=reason)
        actionResult = ActionSuccessResult(outputs=None, success="Action successful")
        self.actionInstances.append(
            ActionInstance(action=ActionVal, result=actionResult, summary="")
        )
        self.index = len(self.actionInstances)

    def register_result(self, result):
        if self.current_action:
            self.current_action.result = result
        else:
            print("No action registered")
        self.index = len(self.actionInstances)

    def rewind(self, num_episodes):
        if self.current_action and self.current_action and not self.current_action.result:
            self.actionInstances.pop(self.index)

        if num_episodes > 0:
            self.actionInstances = self.actionInstances[:-num_episodes]
            self.index = len(self.actionInstances)
