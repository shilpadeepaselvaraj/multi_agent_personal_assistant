import os
import json
import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
import schedule
import time
import threading

# Data Models
@dataclass
class Meeting:
    title: str
    date: datetime.datetime
    duration: int
    attendees: List[str]
    location: str = ""

@dataclass
class TodoItem:
    id: str
    task: str
    priority: str
    due_date: datetime.datetime
    completed: bool = False

@dataclass
class Reminder:
    type: str
    message: str
    time: datetime.time
    days: List[str]  # ['Monday', 'Tuesday', etc.]

# Custom Tools
class MeetingSchedulerTool(BaseTool):
    name: str = "meeting_scheduler"
    description: str = "Schedule, reschedule, or cancel meetings"
    
    def __init__(self):
        super().__init__()
        meetings = []
        self.load_meetings()
    
    def _run(self, action: str, **kwargs) -> str:
        if action == "schedule":
            return self.schedule_meeting(**kwargs)
        elif action == "list":
            return self.list_meetings()
        elif action == "cancel":
            return self.cancel_meeting(kwargs.get('meeting_id'))
        
    def schedule_meeting(self, title: str, date_str: str, duration: int, attendees: List[str], location: str = "") -> str:
        try:
            meeting_date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            meeting = Meeting(title, meeting_date, duration, attendees, location)
            self.meetings.append(meeting)
            self.save_meetings()
            return f"Meeting '{title}' scheduled for {meeting_date.strftime('%Y-%m-%d %H:%M')}"
        except Exception as e:
            return f"Error scheduling meeting: {str(e)}"
    
    def list_meetings(self) -> str:
        if not self.meetings:
            return "No meetings scheduled."
        
        upcoming = [m for m in self.meetings if m.date > datetime.datetime.now()]
        if not upcoming:
            return "No upcoming meetings."
        
        result = "Upcoming meetings:\n"
        for meeting in sorted(upcoming, key=lambda x: x.date):
            result += f"- {meeting.title} on {meeting.date.strftime('%Y-%m-%d %H:%M')} ({meeting.duration} min)\n"
        return result
    
    def save_meetings(self):
        # In a real implementation, save to database or file
        pass
    
    def load_meetings(self):
        # In a real implementation, load from database or file
        pass

class TodoManagerTool(BaseTool):
    name: str = "todo_manager"
    description: str = "Manage todo lists and tasks"
    
    def __init__(self):
        super().__init__()
        todos = []
        self.load_todos()
    
    def _run(self, action: str, **kwargs) -> str:
        if action == "add":
            return self.add_todo(**kwargs)
        elif action == "list":
            return self.list_todos()
        elif action == "complete":
            return self.complete_todo(kwargs.get('task_id'))
        elif action == "priority":
            return self.list_by_priority()
    
    def add_todo(self, task: str, priority: str = "medium", due_date_str: str = None) -> str:
        try:
            due_date = datetime.datetime.now() + datetime.timedelta(days=7)  # Default 1 week
            if due_date_str:
                due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d")
            
            todo = TodoItem(
                id=str(len(self.todos) + 1),
                task=task,
                priority=priority,
                due_date=due_date
            )
            self.todos.append(todo)
            self.save_todos()
            return f"Added task: {task} (Priority: {priority})"
        except Exception as e:
            return f"Error adding todo: {str(e)}"
    
    def list_todos(self) -> str:
        if not self.todos:
            return "No tasks in your todo list."
        
        active_todos = [t for t in self.todos if not t.completed]
        if not active_todos:
            return "All tasks completed!"
        
        result = "Your Todo List:\n"
        for todo in sorted(active_todos, key=lambda x: x.due_date):
            status = "❌" if todo.due_date < datetime.datetime.now() else "⏰"
            result += f"{status} {todo.task} (Priority: {todo.priority}, Due: {todo.due_date.strftime('%Y-%m-%d')})\n"
        return result
    
    def complete_todo(self, task_id: str) -> str:
        for todo in self.todos:
            if todo.id == task_id:
                todo.completed = True
                self.save_todos()
                return f"Task completed: {todo.task}"
        return "Task not found."
    
    def save_todos(self):
        pass
    
    def load_todos(self):
        pass

class ReminderTool(BaseTool):
    name: str = "reminder_system"
    description: str = "Set up reminders for gym, medicine, and other activities"
    
    def __init__(self):
        super().__init__()
        reminders = []
        self.load_reminders()
        self.start_reminder_scheduler()
    
    def _run(self, action: str, **kwargs) -> str:
        if action == "add":
            return self.add_reminder(**kwargs)
        elif action == "list":
            return self.list_reminders()
        elif action == "remove":
            return self.remove_reminder(kwargs.get('reminder_id'))
    
    def add_reminder(self, reminder_type: str, message: str, time_str: str, days: List[str]) -> str:
        try:
            reminder_time = datetime.datetime.strptime(time_str, "%H:%M").time()
            reminder = Reminder(reminder_type, message, reminder_time, days)
            self.reminders.append(reminder)
            self.save_reminders()
            return f"Reminder set: {message} at {time_str} on {', '.join(days)}"
        except Exception as e:
            return f"Error setting reminder: {str(e)}"
    
    def list_reminders(self) -> str:
        if not self.reminders:
            return "No reminders set."
        
        result = "Your Reminders:\n"
        for i, reminder in enumerate(self.reminders):
            result += f"{i+1}. {reminder.message} at {reminder.time.strftime('%H:%M')} on {', '.join(reminder.days)}\n"
        return result
    
    def start_reminder_scheduler(self):
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
    
    def save_reminders(self):
        pass
    
    def load_reminders(self):
        pass

class BlogWritingTool(BaseTool):
    name: str = "blog_writer"
    description: str = "Generate blog posts on various topics"
    
    def _run(self, topic: str, length: str = "medium", style: str = "informative") -> str:
        # This would integrate with an AI writing service or use a local model
        return self.generate_blog_post(topic, length, style)
    
    def generate_blog_post(self, topic: str, length: str, style: str) -> str:
        # Placeholder for blog generation logic
        # In a real implementation, this would use GPT, Claude, or another LLM
        blog_structure = f"""
# Blog Post: {topic}

## Introduction
[Generated introduction about {topic}]

## Main Content
[Generated main content in {style} style, {length} length]

## Conclusion
[Generated conclusion]

---
*Blog post generated on {datetime.datetime.now().strftime('%Y-%m-%d')}*
"""
        return f"Blog post generated for topic: {topic}\n\nStructure:\n{blog_structure}"

# Initialize Tools
meeting_tool = MeetingSchedulerTool()
todo_tool = TodoManagerTool()
reminder_tool = ReminderTool()
blog_tool = BlogWritingTool()

# Define Agents
scheduling_agent = Agent(
    role='Personal Scheduler',
    goal='Efficiently manage and schedule meetings',
    backstory='You are an expert personal assistant specialized in calendar management and scheduling.',
    tools=[meeting_tool],
    verbose=True
)

task_agent = Agent(
    role='Task Manager',
    goal='Organize and track todo items effectively',
    backstory='You are a productivity expert who helps people stay organized and complete their tasks.',
    tools=[todo_tool],
    verbose=True
)

health_agent = Agent(
    role='Health Reminder Assistant',
    goal='Help maintain healthy habits through timely reminders',
    backstory='You are a health-conscious assistant focused on wellness and habit formation.',
    tools=[reminder_tool],
    verbose=True
)

content_agent = Agent(
    role='Content Creator',
    goal='Generate high-quality blog content on various topics',
    backstory='You are a skilled writer who creates engaging and informative blog posts.',
    tools=[blog_tool],
    verbose=True
)

# Main Assistant Class
class PersonalAssistant:
    def __init__(self):
        self.agents = {
            'scheduler': scheduling_agent,
            'tasks': task_agent,
            'health': health_agent,
            'content': content_agent
        }
    
    def schedule_meeting(self, title: str, date: str, duration: int, attendees: List[str], location: str = ""):
        task = Task(
            description=f"Schedule a meeting titled '{title}' for {date} lasting {duration} minutes with {attendees}",
            agent=self.agents['scheduler'],
            expected_output="Confirmation of meeting scheduled"
        )
        
        crew = Crew(
            agents=[self.agents['scheduler']],
            tasks=[task],
            process=Process.sequential
        )
        
        return crew.kickoff()
    
    def add_todo(self, task: str, priority: str = "medium", due_date: str = None):
        task_obj = Task(
            description=f"Add todo item: {task} with priority {priority}",
            agent=self.agents['tasks'],
            expected_output="Confirmation of task added"
        )
        
        crew = Crew(
            agents=[self.agents['tasks']],
            tasks=[task_obj],
            process=Process.sequential
        )
        
        return crew.kickoff()
    
    def set_reminder(self, reminder_type: str, message: str, time: str, days: List[str]):
        task = Task(
            description=f"Set {reminder_type} reminder: {message} at {time} on {days}",
            agent=self.agents['health'],
            expected_output="Confirmation of reminder set"
        )
        
        crew = Crew(
            agents=[self.agents['health']],
            tasks=[task],
            process=Process.sequential
        )
        
        return crew.kickoff()
    
    def write_blog(self, topic: str, length: str = "medium", style: str = "informative"):
        task = Task(
            description=f"Write a {length} blog post about {topic} in {style} style",
            agent=self.agents['content'],
            expected_output="Complete blog post"
        )
        
        crew = Crew(
            agents=[self.agents['content']],
            tasks=[task],
            process=Process.sequential
        )
        
        return crew.kickoff()
    
    def daily_briefing(self):
        """Get a comprehensive daily briefing from all agents"""
        tasks = [
            Task(
                description="List today's meetings and upcoming schedule",
                agent=self.agents['scheduler'],
                expected_output="Meeting schedule summary"
            ),
            Task(
                description="Show current todo list with priorities",
                agent=self.agents['tasks'],
                expected_output="Todo list summary"
            ),
            Task(
                description="List active reminders for today",
                agent=self.agents['health'],
                expected_output="Reminder summary"
            )
        ]
        
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            process=Process.sequential
        )
        
        return crew.kickoff()

# Usage Example
if __name__ == "__main__":
    assistant = PersonalAssistant()
    
    # Example usage
    print("=== Personal Assistant Demo ===\n")
    
    # Schedule a meeting
    print("1. Scheduling a meeting...")
    result = assistant.schedule_meeting(
        title="Project Review",
        date="2024-06-10 14:00",
        duration=60,
        attendees=["john@example.com", "jane@example.com"],
        location="Conference Room A"
    )
    print(f"Result: {result}\n")
    
    # Add todo items
    print("2. Adding todo items...")
    assistant.add_todo("Complete project documentation", "high", "2024-06-08")
    assistant.add_todo("Review code changes", "medium", "2024-06-09")
    print("Todo items added.\n")
    
    # Set reminders
    print("3. Setting up reminders...")
    assistant.set_reminder("gym", "Time to go to the gym!", "18:00", ["Monday", "Wednesday", "Friday"])
    assistant.set_reminder("medicine", "Take your evening medication", "20:00", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    print("Reminders set.\n")
    
    # Generate a blog post
    print("4. Writing a blog post...")
    blog_result = assistant.write_blog("The Future of AI in Personal Productivity", "long", "informative")
    print(f"Blog generated: {blog_result}\n")
    
    # Get daily briefing
    print("5. Daily briefing...")
    briefing = assistant.daily_briefing()
    print(f"Daily briefing: {briefing}")