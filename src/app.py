import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
from openai import OpenAI

class WorldOfWarcraft:
    def __init__(self):
        """Initializes the window & more"""
        self.window = tk.Tk()
        self.window.title("World Of Warcraft")
        self.window.geometry("800x600")
        self.window.resizable(False, False)
        
        self.users_file = "users.json"
        self.lobbies_file = "lobbies.json"
        
        # Current user that logs in
        self.current_user = None
        
        # Initialize AI client       
        self.ai_client = OpenAI(base_url='https://api.gapgpt.app/v1', api_key='api')
        
        self.InitDataFiles()
        self.ShowLoginScreen()
    
    def InitDataFiles(self):
        """Create JSON files if they don't exist"""
        if not os.path.exists("data"):
            os.makedirs("data")
            
        if not os.path.exists(f"data/{self.users_file}"):
            json.dump({}, open(f"data/{self.users_file}", 'w')
)
        
        if not os.path.exists(f"data/{self.lobbies_file}"):
            json.dump({}, open(f"data/{self.lobbies_file}", 'w')
)
    
    def LoadUsers(self):    
        """Load usrs from JSON file"""
        try:
            content = open(f"data/{self.users_file}", 'r').read().strip()
            if not content:
                return {}
            return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def SaveUsers(self, users):
        """Save users to JSON file"""
        try:
            json.dump(users, open(f"data/{self.users_file}", 'w'), indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save users: {str(e)}")
    
    def LoadLobbies(self):
        """Load lobbies from JSON file"""
        try:
            content = open(f"data/{self.lobbies_file}", 'r').read().strip()
            if not content:
                return {}
            return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def SaveLobbies(self, lobbies):
        """Save lobbies to JSON fil"""
        try:
            json.dump(lobbies, open(f"data/{self.lobbies_file}", 'w'), indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save lobbies: {str(e)}")
    
    def GetAILobbySuggestions(self):
        """Get AI lobby suggestions using OpenAi Inference API"""
        try:
            lobbies = self.LoadLobbies()
            if not lobbies:
                return "No lobbies available for analysis."

            # Prepare lobby data
            available_lobbies = []
            for lobby_id, lobby in lobbies.items():
                if self.CanJoinLobby(lobby) and not self.IsMemberOfLobby(lobby):
                    roles_needed = []
                    if lobby['members']['Tank'] is None:
                        roles_needed.append("Tank")
                    if lobby['members']['Healer'] is None:
                        roles_needed.append("Healer")
                    dps_null_count = lobby['members']['DPS'].count(None)
                    if dps_null_count > 0:
                        roles_needed.append(f"{dps_null_count} DPS")

                    available_lobbies.append({
                        "name": lobby['name'],
                        "leader": lobby['leader'],
                        "required_rating": lobby['required_rating'],
                        "roles_needed": ", ".join(roles_needed),
                        "rating_diff": self.current_user['rating'] - lobby['required_rating']
                    })

            if not available_lobbies:
                return "No suitable lobbies found for your rating and role."

            # Format lobby information
            lobbies_info = []
            for lobby in available_lobbies:
                rating_status = f"+{lobby['rating_diff']}" if lobby['rating_diff'] >= 0 else f"{lobby['rating_diff']}"
                lobbies_info.append(
                    f"- {lobby['name']} (Leader: {lobby['leader']}) "
                    f"| Needs: {lobby['roles_needed']} "
                    f"| Req Rating: {lobby['required_rating']} (Your rating: {rating_status})"
                )
            lobbies_text = "\n".join(lobbies_info)

            # Create optimized prompt
            prompt = f"""
[INST] As a World of Warcraft matchmaking expert, recommend the best lobby for this player:

Player Info:
- Role: {self.current_user['role']}
- Rating: {self.current_user['rating']}

Available Lobbies:
{lobbies_text}

Recommend ONE lobby and explain why in ten sentence.
explain the roles of anybody in the game
Format your response as:
Recommended: [Lobby Name]
Reason: [Brief explanation]
[/INST]
"""
            # Get AI suggestions
            response = self.ai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"⚠️ AI Error: {str(e)}"

    def ShowAISuggestions(self):
        """Display AI lobby suggestions in a new window"""
        suggestions_window = tk.Toplevel(self.window)
        suggestions_window.title("AI Lobby Suggestions")
        suggestions_window.geometry("600x500")
        suggestions_window.transient(self.window)
        
        # Title
        title_label = tk.Label(suggestions_window, text="🤖 AI Lobby Recommendations", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Loading message
        loading_label = tk.Label(suggestions_window, text="Analyzing lobbies with AI...", 
                                font=("Arial", 12))
        loading_label.pack(pady=20)
        
        # Create text widget for suggestions
        text_frame = tk.Frame(suggestions_window)
        text_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        text_widget = tk.Text(text_frame, wrap='word', font=("Arial", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        tk.Button(suggestions_window, text="Close", command=suggestions_window.destroy,
                 bg="gray", fg="white").pack(pady=5)
        
        # Get AI suggestions in a separate thread to avoid freezing UI
        def GetSuggestion():
            loading_label.config(text="Getting AI recommendations...")
            suggestions_window.update()
            
            suggestions = self.GetAILobbySuggestions()
            
            # Update the text widget
            text_widget.delete(1.0, tk.END)
            text_widget.insert(1.0, suggestions)
            text_widget.config(state='disabled')  # Make it read-only
            
            loading_label.destroy()
        
        # Call after a short delay to let window render
        suggestions_window.after(100, GetSuggestion)
    
    def ClearWindow(self):
        """Clear all widgets from the window"""
        for widget in self.window.winfo_children():
            widget.destroy()
    
    def ShowLoginScreen(self):
        """Display the login/register screen"""
        self.ClearWindow()
        
        main_frame = tk.Frame(self.window)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        title_label = tk.Label(main_frame, text="World Of Warcraft", font=("Arial", 20, "bold"))
        title_label.pack(pady=20)
        
        # Login/Register toggle
        self.is_register_mode = tk.BooleanVar()
        toggle_frame = tk.Frame(main_frame)
        toggle_frame.pack(pady=10)
        
        tk.Radiobutton(toggle_frame, text="Sign In", variable=self.is_register_mode, 
                      value=False, command=self.ToggleMode).pack(side='left', padx=10)
        tk.Radiobutton(toggle_frame, text="Register", variable=self.is_register_mode, 
                      value=True, command=self.ToggleMode).pack(side='left', padx=10)
        
        # Form frame
        self.form_frame = tk.Frame(main_frame)
        self.form_frame.pack(pady=20)
        
        self.CreateLoginForm()
    
    def ToggleMode(self):
        """Toggle between login and register mode"""
        self.CreateLoginForm()
    
    def CreateLoginForm(self):
        """Create the login/register form"""
        # Clear form frame instead of entire window
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.form_frame, text="Username:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.username_entry = tk.Entry(self.form_frame, width=25)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(self.form_frame, text="Password:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.password_entry = tk.Entry(self.form_frame, width=25, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        if self.is_register_mode.get():
            tk.Label(self.form_frame, text="Gmail:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
            self.email_entry = tk.Entry(self.form_frame, width=25)
            self.email_entry.grid(row=2, column=1, padx=5, pady=5)
            
            tk.Label(self.form_frame, text="Role:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
            self.role_var = tk.StringVar(value="DPS")
            role_frame = tk.Frame(self.form_frame)
            role_frame.grid(row=3, column=1, padx=5, pady=5)
            
            tk.Radiobutton(role_frame, text="Tank", variable=self.role_var, value="Tank").pack(side='left')
            tk.Radiobutton(role_frame, text="Healer", variable=self.role_var, value="Healer").pack(side='left')
            tk.Radiobutton(role_frame, text="DPS", variable=self.role_var, value="DPS").pack(side='left')
            
            tk.Label(self.form_frame, text="Rating (0-4000):").grid(row=4, column=0, sticky='e', padx=5, pady=5)
            self.rating_entry = tk.Entry(self.form_frame, width=25)
            self.rating_entry.grid(row=4, column=1, padx=5, pady=5)
            
            tk.Button(self.form_frame, text="Register", command=self.RegisterUser, 
                     bg="green", fg="white").grid(row=5, column=1, pady=20)
        else:
            tk.Button(self.form_frame, text="Sign In", command=self.LoginUser, 
                     bg="blue", fg="white").grid(row=2, column=1, pady=20)
    
    def RegisterUser(self):
        """Register a new user"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        email = self.email_entry.get().strip()
        role = self.role_var.get()
        rating = self.rating_entry.get().strip()
        
        if not all([username, password, email, rating]):
            messagebox.showerror("Error", "All fields are required!")
            return
        
        if not email.endswith("@gmail.com"):
            messagebox.showerror("Error", "Please enter a valid Gmail address!")
            return
        
        try:
            rating = int(rating)
            if rating < 0 or rating > 4000:
                messagebox.showerror("Error", "Rating must be between 0 and 4000!")
                return
        except ValueError:
            messagebox.showerror("Error", "Rating must be a number!")
            return
        
        users = self.LoadUsers()
        if username in users:
            messagebox.showerror("Error", "Username already exists!")
            return
        
        users[username] = {
            "password": password,
            "email": email,
            "role": role,
            "rating": rating,
            "created_at": datetime.now().isoformat()
        }
        self.SaveUsers(users)
        
        messagebox.showinfo("Success", "Registration successful! You can now sign in.")
        self.is_register_mode.set(False)
        self.ToggleMode()
    
    def LoginUser(self):
        """Login user"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required!")
            return
        
        users = self.LoadUsers()
        if username not in users or users[username]["password"] != password:
            messagebox.showerror("Error", "Invalid username or password!")
            return
        
        self.current_user = {
            "username": username,
            **users[username]
        }
        
        self.ShowMainApp()
    
    def ShowMainApp(self):
        """Show the main application with tabs"""
        self.ClearWindow()
        
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.CreateProfileTab()
        self.CreateLobbiesTab()
        
        logout_btn = tk.Button(self.window, text="Logout", command=self.Logout, 
                              bg="red", fg="white")
        logout_btn.pack(pady=5)
    
    def CreateProfileTab(self):
        """Create the profile tab"""
        profile_frame = ttk.Frame(self.notebook)
        self.notebook.add(profile_frame, text="Profile")
        
        info_frame = tk.Frame(profile_frame)
        info_frame.pack(padx=20, pady=20)
        
        tk.Label(info_frame, text="Profile Information", font=("Arial", 16, "bold")).pack(pady=10)
        
        tk.Label(info_frame, text=f"Username: {self.current_user['username']}", 
                font=("Arial", 12)).pack(pady=5, anchor='w')
        tk.Label(info_frame, text=f"Email: {self.current_user['email']}", 
                font=("Arial", 12)).pack(pady=5, anchor='w')
        tk.Label(info_frame, text=f"Role: {self.current_user['role']}", 
                font=("Arial", 12)).pack(pady=5, anchor='w')
        tk.Label(info_frame, text=f"Rating: {self.current_user['rating']}", 
                font=("Arial", 12)).pack(pady=5, anchor='w')
    
    def CreateLobbiesTab(self):
        """Create the lobbies tab"""
        lobbies_frame = ttk.Frame(self.notebook)
        self.notebook.add(lobbies_frame, text="Lobbies")
        
        top_frame = tk.Frame(lobbies_frame)
        top_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(top_frame, text="Create Lobby", command=self.CreateLobbyDialog, 
                 bg="green", fg="white").pack(side='left')
        tk.Button(top_frame, text="Refresh", command=self.RefreshLobbies, 
                 bg="blue", fg="white").pack(side='left', padx=10)
        tk.Button(top_frame, text="🤖 AI Suggestions", command=self.ShowAISuggestions, 
                 bg="purple", fg="white").pack(side='left', padx=10)
        
        self.lobbies_listbox_frame = tk.Frame(lobbies_frame)
        self.lobbies_listbox_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.RefreshLobbies()
    
    def IsUserInAnyLobby(self):
        """Check if current user is already in any lobby"""
        lobbies = self.LoadLobbies()
        username = self.current_user['username']
        
        for lobby in lobbies.values():
            if self.IsMemberOfLobby(lobby):
                return True
        return False

    def CreateLobbyDialog(self):
        """Show create lobby dialog"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Create Lobby")
        dialog.geometry("300x200")
        dialog.transient(self.window)
        dialog.grab_set()
        
        tk.Label(dialog, text="Lobby Name:").pack(pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Required Rating:").pack(pady=5)
        rating_entry = tk.Entry(dialog, width=30)
        rating_entry.pack(pady=5)
        
        def CreateLobby():
            name = name_entry.get().strip()
            try:
                required_rating = int(rating_entry.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Rating must be a number!")
                return
            
            if not name:
                messagebox.showerror("Error", "Lobby name is required!")
                return
            
            if required_rating < 0 or required_rating > 4000:
                messagebox.showerror("Error", "Rating must be between 0 and 4000!")
                return
            
            if self.IsUserInAnyLobby():
                messagebox.showerror("Error", "You're already in a lobby! Leave your current lobby before creating a new one.")
                return

            lobbies = self.LoadLobbies()
            
            # Check if lobby name exists
            if name in lobbies:
                messagebox.showerror("Error", "Lobby name already exists!")
                return
            
            # Create lobby
            lobby_id = name
            lobbies[lobby_id] = {
                "name": name,
                "leader": self.current_user["username"],
                "required_rating": required_rating,
                "members": {
                    "Tank": None,
                    "Healer": None,
                    "DPS": [None, None, None]
                },
                "created_at": datetime.now().isoformat()
            }
            
            # Add creator to lobby
            if self.current_user["role"] == "DPS":
                for i in range(3):
                    if lobbies[lobby_id]["members"]["DPS"][i] is None:
                        lobbies[lobby_id]["members"]["DPS"][i] = self.current_user["username"]
                        break
            else:
                lobbies[lobby_id]["members"][self.current_user["role"]] = self.current_user["username"]
            
            self.SaveLobbies(lobbies)
            dialog.destroy()
            self.RefreshLobbies()
            messagebox.showinfo("Success", "Lobby created successfully!")
        
        tk.Button(dialog, text="Create", command=CreateLobby, 
                 bg="green", fg="white").pack(pady=20)
    
    def RefreshLobbies(self):
        """Refresh the lobbies list"""
        # Clear existing widgets
        for widget in self.lobbies_listbox_frame.winfo_children():
            widget.destroy()
        
        lobbies = self.LoadLobbies()
        
        if not lobbies:
            tk.Label(self.lobbies_listbox_frame, text="No lobbies available", 
                    font=("Arial", 12)).pack(pady=20)
            return
        
        # Create scrollable frame
        canvas = tk.Canvas(self.lobbies_listbox_frame)
        scrollbar = ttk.Scrollbar(self.lobbies_listbox_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add lobbies
        for lobby_id, lobby in lobbies.items():
            self.CreateLobbyWidget(scrollable_frame, lobby_id, lobby)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def CreateLobbyWidget(self, parent, lobby_id, lobby):
        """Create a widget for a single lobby"""
        frame = tk.Frame(parent, relief="ridge", bd=2)
        frame.pack(fill='x', padx=5, pady=5)
        
        # Lobby info
        info_frame = tk.Frame(frame)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(info_frame, text=f"Lobby: {lobby['name']}", 
                font=("Arial", 12, "bold")).pack(anchor='w')
        tk.Label(info_frame, text=f"Leader: {lobby['leader']}", 
                font=("Arial", 10)).pack(anchor='w')
        tk.Label(info_frame, text=f"Required Rating: {lobby['required_rating']}", 
                font=("Arial", 10)).pack(anchor='w')
        
        # Members info
        members_frame = tk.Frame(frame)
        members_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(members_frame, text="Members:", font=("Arial", 10, "bold")).pack(anchor='w')
        
        tank = lobby['members']['Tank'] or "Empty"
        healer = lobby['members']['Healer'] or "Empty"
        dps_list = [member or "Empty" for member in lobby['members']['DPS']]
        
        tk.Label(members_frame, text=f"Tank: {tank}").pack(anchor='w')
        tk.Label(members_frame, text=f"Healer: {healer}").pack(anchor='w')
        tk.Label(members_frame, text=f"DPS: {', '.join(dps_list)}").pack(anchor='w')
        
        # Buttons
        button_frame = tk.Frame(frame)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        # Check if user can join
        can_join = self.CanJoinLobby(lobby)
        is_member = self.IsMemberOfLobby(lobby)
        is_leader = lobby['leader'] == self.current_user['username']
        
        if is_leader:
            tk.Button(button_frame, text="Delete Lobby", 
                     command=lambda: self.DeleteLobby(lobby_id),
                     bg="red", fg="white").pack(side='left', padx=5)
        elif is_member:
            tk.Button(button_frame, text="Leave Lobby", 
                     command=lambda: self.LeaveLobby(lobby_id),
                     bg="orange", fg="white").pack(side='left', padx=5)
        elif can_join:
            tk.Button(button_frame, text="Join Lobby", 
                     command=lambda: self.JoinLobby(lobby_id),
                     bg="blue", fg="white").pack(side='left', padx=5)
        else:
            reason = self.JoinRestrictionReason(lobby)
            tk.Label(button_frame, text=f"Cannot join: {reason}", 
                    fg="red").pack(side='left', padx=5)
    
    def CanJoinLobby(self, lobby):
        """Check if current user can join the lobby"""
        # Check rating requirement
        if self.current_user['rating'] < lobby['required_rating']:
            return False
        
        # Check if role slot is available
        role = self.current_user['role']
        if role == "DPS":
            return None in lobby['members']['DPS']
        else:
            return lobby['members'][role] is None
    
    def IsMemberOfLobby(self, lobby):
        """Check if current user is already a member of the lobby"""
        username = self.current_user['username']
        if lobby['members']['Tank'] == username or lobby['members']['Healer'] == username:
            return True
        return username in lobby['members']['DPS']
    
    def JoinRestrictionReason(self, lobby):
        """Get the reason why user cannot join the lobby"""
        if self.current_user['rating'] < lobby['required_rating']:
            return "Rating too low"
        
        role = self.current_user['role']
        if role == "DPS":
            if None not in lobby['members']['DPS']:
                return "DPS slots full"
        else:
            if lobby['members'][role] is not None:
                return f"{role} slot taken"
        
        return "Unknown reason"
    
    def JoinLobby(self, lobby_id):
        """Join a lobby"""
        if self.IsUserInAnyLobby():
            messagebox.showerror("Error", "You're already in a lobby! Leave your current lobby before joining another one.")
            return
            
        lobbies = self.LoadLobbies()
        lobby = lobbies[lobby_id]
        username = self.current_user['username']
        role = self.current_user['role']
        
        if role == "DPS":
            for i in range(3):
                if lobby['members']['DPS'][i] is None:
                    lobby['members']['DPS'][i] = username
                    break
        else:
            lobby['members'][role] = username
        
        self.SaveLobbies(lobbies)
        self.RefreshLobbies()
        messagebox.showinfo("Success", "Joined lobby successfully!")
    
    def LeaveLobby(self, lobby_id):
        """Leave a lobby"""
        lobbies = self.LoadLobbies()
        lobby = lobbies[lobby_id]
        username = self.current_user['username']
        
        # Remove user from lobby
        if lobby['members']['Tank'] == username:
            lobby['members']['Tank'] = None
        elif lobby['members']['Healer'] == username:
            lobby['members']['Healer'] = None
        else:
            for i in range(3):
                if lobby['members']['DPS'][i] == username:
                    lobby['members']['DPS'][i] = None
                    break
        
        self.SaveLobbies(lobbies)
        self.RefreshLobbies()
        messagebox.showinfo("Success", "Left lobby successfully!")
    
    def DeleteLobby(self, lobby_id):
        """Delete a lobby (leader only)"""
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this lobby?"):
            lobbies = self.LoadLobbies()
            del lobbies[lobby_id]
            self.SaveLobbies(lobbies)
            self.RefreshLobbies()
            messagebox.showinfo("Success", "Lobby deleted successfully!")
    
    def Logout(self):
        """Logout user"""
        self.current_user = None
        self.ShowLoginScreen()
    
    def Run(self):
        """Run the application"""
        self.window.mainloop()