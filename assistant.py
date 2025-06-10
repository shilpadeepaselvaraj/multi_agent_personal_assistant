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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Global storage for demonstration (in a real app, use a database)
meetings_storage = []
todos_storage = []
reminders_storage = []

# Custom Tools - Using BaseTool class for compatibility
class MeetingSchedulerTool(BaseTool):
    name: str = "meeting_scheduler"
    description: str = "Schedule, reschedule, or cancel meetings"
    
    def _run(self, action: str, **kwargs) -> str:
        global meetings_storage
        
        if action == "schedule":
            title = kwargs.get('title', '')
            date_str = kwargs.get('date_str', '')
            duration = kwargs.get('duration', 60)
            attendees = kwargs.get('attendees', [])
            location = kwargs.get('location', '')
            
            try:
                meeting_date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                meeting = {
                    'id': len(meetings_storage) + 1,
                    'title': title,
                    'date': meeting_date,
                    'duration': duration,
                    'attendees': attendees,
                    'location': location
                }
                meetings_storage.append(meeting)
                return f"Meeting '{title}' scheduled for {meeting_date.strftime('%Y-%m-%d %H:%M')} with {', '.join(attendees)}"
            except Exception as e:
                return f"Error scheduling meeting: {str(e)}"
        
        elif action == "list":
            if not meetings_storage:
                return "No meetings scheduled."
            
            result = "Upcoming meetings:\n"
            for meeting in meetings_storage:
                result += f"- {meeting['title']} on {meeting['date'].strftime('%Y-%m-%d %H:%M')} ({meeting['duration']} min)\n"
            return result
        
        elif action == "cancel":
            meeting_id = kwargs.get('meeting_id', '')
            try:
                meeting_id = int(meeting_id)
                meetings_storage = [m for m in meetings_storage if m['id'] != meeting_id]
                return f"Meeting {meeting_id} has been cancelled"
            except:
                return "Invalid meeting ID"
        
        return "Invalid action specified"

class TodoManagerTool(BaseTool):
    name: str = "todo_manager"
    description: str = "Manage todo lists and tasks"
    
    def _run(self, action: str, **kwargs) -> str:
        global todos_storage
        
        if action == "add":
            task = kwargs.get('task', '')
            priority = kwargs.get('priority', 'medium')
            due_date_str = kwargs.get('due_date_str', '')
            
            try:
                due_date = datetime.datetime.now() + datetime.timedelta(days=7)  # Default 1 week
                if due_date_str:
                    due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d")
                
                todo = {
                    'id': len(todos_storage) + 1,
                    'task': task,
                    'priority': priority,
                    'due_date': due_date,
                    'completed': False
                }
                todos_storage.append(todo)
                return f"Added task: {task} (Priority: {priority})"
            except Exception as e:
                return f"Error adding task: {str(e)}"
        
        elif action == "list":
            if not todos_storage:
                return "No tasks in your todo list."
            
            active_todos = [t for t in todos_storage if not t['completed']]
            if not active_todos:
                return "All tasks completed!"
            
            result = "Your Todo List:\n"
            for todo in active_todos:
                status = "❌" if todo['due_date'] < datetime.datetime.now() else "⏰"
                result += f"{status} {todo['task']} (Priority: {todo['priority']}, Due: {todo['due_date'].strftime('%Y-%m-%d')})\n"
            return result
        
        elif action == "complete":
            task_id = kwargs.get('task_id', '')
            try:
                task_id = int(task_id)
                for todo in todos_storage:
                    if todo['id'] == task_id:
                        todo['completed'] = True
                        return f"Task completed: {todo['task']}"
                return "Task not found"
            except:
                return "Invalid task ID"
        
        return "Invalid action specified"

class ReminderTool(BaseTool):
    name: str = "reminder_system"
    description: str = "Set up reminders for gym, medicine, and other activities"
    
    def _run(self, action: str, **kwargs) -> str:
        global reminders_storage
        
        if action == "add":
            reminder_type = kwargs.get('reminder_type', '')
            message = kwargs.get('message', '')
            time_str = kwargs.get('time_str', '')
            days = kwargs.get('days', [])
            
            try:
                reminder_time = datetime.datetime.strptime(time_str, "%H:%M").time()
                reminder = {
                    'id': len(reminders_storage) + 1,
                    'type': reminder_type,
                    'message': message,
                    'time': reminder_time,
                    'days': days
                }
                reminders_storage.append(reminder)
                return f"Reminder set: {message} at {time_str} on {', '.join(days)}"
            except Exception as e:
                return f"Error setting reminder: {str(e)}"
        
        elif action == "list":
            if not reminders_storage:
                return "No reminders set."
            
            result = "Your Reminders:\n"
            for reminder in reminders_storage:
                result += f"{reminder['id']}. {reminder['message']} at {reminder['time'].strftime('%H:%M')} on {', '.join(reminder['days'])}\n"
            return result
        
        elif action == "remove":
            reminder_id = kwargs.get('reminder_id', '')
            try:
                reminder_id = int(reminder_id)
                reminders_storage = [r for r in reminders_storage if r['id'] != reminder_id]
                return f"Reminder {reminder_id} removed"
            except:
                return "Invalid reminder ID"
        
        return "Invalid action specified"

class BlogWriterTool(BaseTool):
    name: str = "blog_writer"
    description: str = "Generate blog posts on various topics"
    
    def _run(self, topic: str, length: str = "medium", style: str = "informative") -> str:
        blog_structure = f"""
# Blog Post: {topic}

## Introduction
In today's rapidly evolving digital landscape, {topic} has become increasingly important...

## Main Content
[This would be a {length} length article written in {style} style about {topic}]

Key points to cover:
- Current trends and developments
- Practical applications and benefits
- Future implications and considerations
- Best practices and recommendations

## Conclusion
As we look toward the future, {topic} will continue to play a crucial role...

---
*Blog post generated on {datetime.datetime.now().strftime('%Y-%m-%d')}*
"""
        return f"Blog post generated for topic: {topic}\n\nStructure:\n{blog_structure}"

# Initialize tool instances
meeting_tool = MeetingSchedulerTool()
todo_tool = TodoManagerTool()
reminder_tool = ReminderTool()
blog_tool = BlogWriterTool()

# Define Agents with proper LLM configuration
def create_agents():
    # Set default LLM model - you might need to configure this based on your setup
    # For local development, you might want to use a local model or ensure API keys are set
    
    scheduling_agent = Agent(
        role='Personal Scheduler',
        goal='Efficiently manage and schedule meetings',
        backstory='You are an expert personal assistant specialized in calendar management and scheduling.',
        tools=[meeting_tool],  # FIXED: Use instance instead of class
        verbose=True,
        allow_delegation=False
    )

    task_agent = Agent(
        role='Task Manager',
        goal='Organize and track todo items effectively',
        backstory='You are a productivity expert who helps people stay organized and complete their tasks.',
        tools=[todo_tool],  # FIXED: Use instance instead of class
        verbose=True,
        allow_delegation=False
    )

    health_agent = Agent(
        role='Health Reminder Assistant',
        goal='Help maintain healthy habits through timely reminders',
        backstory='You are a health-conscious assistant focused on wellness and habit formation.',
        tools=[reminder_tool],  # FIXED: Use instance instead of class
        verbose=True,
        allow_delegation=False
    )

    content_agent = Agent(
        role='Content Creator',
        goal='Generate high-quality blog content on various topics',
        backstory='You are a skilled writer who creates engaging and informative blog posts.',
        tools=[blog_tool],  # FIXED: Use instance instead of class
        verbose=True,
        allow_delegation=False
    )
    
    return {
        'scheduler': scheduling_agent,
        'tasks': task_agent,
        'health': health_agent,
        'content': content_agent
    }

# Main Assistant Class
class PersonalAssistant:
    def __init__(self):
        # Check for required environment variables
        self.check_environment()
        self.agents = create_agents()
    
    def check_environment(self):
        """Check if required environment variables are set"""
        required_vars = ['OPENAI_API_KEY']  # Add other required API keys as needed
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
            print("Please set these in your .env file or environment")
            print("Example .env file content:")
            print("OPENAI_API_KEY=your_openai_api_key_here")
    
    def schedule_meeting(self, title: str, date: str, duration: int, attendees: List[str], location: str = ""):
        try:
            task = Task(
                description=f"Schedule a meeting titled '{title}' for {date} lasting {duration} minutes with attendees: {', '.join(attendees)} at location: {location}",
                agent=self.agents['scheduler'],
                expected_output="Confirmation message that the meeting has been scheduled with all details"
            )
            
            crew = Crew(
                agents=[self.agents['scheduler']],
                tasks=[task],
                process=Process.sequential,
                verbose=True
            )
            
            return crew.kickoff()
        except Exception as e:
            return f"Error scheduling meeting: {str(e)}"
    
    def add_todo(self, task: str, priority: str = "medium", due_date: str = None):
        try:
            task_obj = Task(
                description=f"Add a new todo item: '{task}' with priority level '{priority}' and due date '{due_date}'",
                agent=self.agents['tasks'],
                expected_output="Confirmation that the task has been added to the todo list"
            )
            
            crew = Crew(
                agents=[self.agents['tasks']],
                tasks=[task_obj],
                process=Process.sequential,
                verbose=True
            )
            
            return crew.kickoff()
        except Exception as e:
            return f"Error adding todo: {str(e)}"
    
    def set_reminder(self, reminder_type: str, message: str, time: str, days: List[str]):
        try:
            task = Task(
                description=f"Set up a {reminder_type} reminder with message '{message}' at time {time} on days: {', '.join(days)}",
                agent=self.agents['health'],
                expected_output="Confirmation that the reminder has been set up"
            )
            
            crew = Crew(
                agents=[self.agents['health']],
                tasks=[task],
                process=Process.sequential,
                verbose=True
            )
            
            return crew.kickoff()
        except Exception as e:
            return f"Error setting reminder: {str(e)}"
    
    def write_blog(self, topic: str, length: str = "medium", style: str = "informative"):
        try:
            task = Task(
                description=f"Write a {length}-length blog post about '{topic}' in {style} style",
                agent=self.agents['content'],
                expected_output="A complete blog post with title, introduction, main content, and conclusion"
            )
            
            crew = Crew(
                agents=[self.agents['content']],
                tasks=[task],
                process=Process.sequential,
                verbose=True
            )
            
            return crew.kickoff()
        except Exception as e:
            return f"Error writing blog: {str(e)}"
    
    def daily_briefing(self):
        """Get a comprehensive daily briefing from all agents"""
        try:
            tasks = [
                Task(
                    description="Provide today's meeting schedule and upcoming appointments",
                    agent=self.agents['scheduler'],
                    expected_output="A summary of today's meetings and schedule"
                ),
                Task(
                    description="Show the current todo list with task priorities and due dates",
                    agent=self.agents['tasks'],
                    expected_output="A summary of pending tasks organized by priority"
                ),
                Task(
                    description="List all active reminders scheduled for today",
                    agent=self.agents['health'],
                    expected_output="A summary of today's reminders and health activities"
                )
            ]
            
            crew = Crew(
                agents=[self.agents['scheduler'], self.agents['tasks'], self.agents['health']],
                tasks=tasks,
                process=Process.sequential,
                verbose=True
            )
            
            return crew.kickoff()
        except Exception as e:
            return f"Error generating daily briefing: {str(e)}"

# Usage Example with better error handling
def main():
    try:
        assistant = PersonalAssistant()
        
        print("=== Personal Assistant Demo ===\n")
        
        # Example usage with error handling
        print("1. Scheduling a meeting...")
        try:
            result = assistant.schedule_meeting(
                title="Project Review",
                date="2024-06-10 14:00",
                duration=60,
                attendees=["john@example.com", "jane@example.com"],
                location="Conference Room A"
            )
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Failed to schedule meeting: {e}\n")
        
        # Add todo items
        print("2. Adding todo items...")
        try:
            result = assistant.add_todo("Complete project documentation", "high", "2024-06-08")
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Failed to add todo: {e}\n")
        
        # Set reminders
        print("3. Setting up reminders...")
        try:
            result = assistant.set_reminder("gym", "Time to go to the gym!", "18:00", ["Monday", "Wednesday", "Friday"])
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Failed to set reminder: {e}\n")
        
        # Generate a blog post
        print("4. Writing a blog post...")
        try:
            result = assistant.write_blog("The Future of AI in Personal Productivity", "long", "informative")
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Failed to write blog: {e}\n")
        
        # Get daily briefing
        print("5. Daily briefing...")
        try:
            result = assistant.daily_briefing()
            print(f"Result: {result}")
        except Exception as e:
            print(f"Failed to generate briefing: {e}")
            
    except Exception as e:
        print(f"Failed to initialize Personal Assistant: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have set your API keys in environment variables")
        print("2. Install required packages: pip install crewai crewai-tools python-dotenv")
        print("3. Create a .env file with your API keys")

if __name__ == "__main__":
    main()