from typing import Any, List, Dict, Optional, Union
import httpx
import json
from mcp.server.fastmcp import FastMCP
import random
import asyncio
import os

load_dotenv()

# Create a FastMCP server instance
mcp = FastMCP("exercisedb")

# ExerciseDB API configuration
EXERCISEDB_API_HOST = "exercisedb.p.rapidapi.com"
API_BASE_URL = f"https://{EXERCISEDB_API_HOST}"

# Get API key from environment variable
RAPIDAPI_KEY = os.getenv("API_KEY")

# Headers for API requests
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": EXERCISEDB_API_HOST,
    "Accept": "application/json"
}

# Cache for API responses to improve performance
_cache = {}

async def make_api_request(endpoint: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
    """Make a request to the ExerciseDB API with caching support"""
    cache_key = f"{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
    
    if use_cache and cache_key in _cache:
        return _cache[cache_key]
    
    url = f"{API_BASE_URL}{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=HEADERS, params=params or {}, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            if use_cache:
                _cache[cache_key] = data
            
            return data
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code}")
            if e.response.status_code == 401:
                print("Authentication failed. Please check your RapidAPI key.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

def format_exercise_list(exercises: List[Dict[str, Any]], limit: int = 10, show_gif: bool = True) -> str:
    """Format a list of exercises for display with GIF URLs"""
    if not exercises:
        return "No exercises found."
    
    # Limit the number of exercises to display
    display_exercises = exercises[:limit]
    
    formatted_exercises = []
    for i, exercise in enumerate(display_exercises, 1):
        gif_section = ""
        if show_gif and exercise.get('gifUrl'):
            gif_section = f"\n- **Visual Guide (GIF):** {exercise.get('gifUrl')}"
        
        formatted = f"""
**{i}. {exercise.get('name', 'Unknown Exercise')}**
- **ID:** {exercise.get('id', 'N/A')}
- **Body Part:** {exercise.get('bodyPart', 'N/A').title()}
- **Target Muscle:** {exercise.get('target', 'N/A').title()}
- **Equipment:** {exercise.get('equipment', 'N/A').title()}
- **Instructions:** {exercise.get('instructions', ['No instructions available'])[0][:100] + '...' if exercise.get('instructions') and len(exercise.get('instructions')[0]) > 100 else exercise.get('instructions', ['No instructions available'])[0] if exercise.get('instructions') else 'No instructions available'}{gif_section}
"""
        formatted_exercises.append(formatted.strip())
    
    result = "\n\n".join(formatted_exercises)
    
    if len(exercises) > limit:
        result += f"\n\n... and {len(exercises) - limit} more exercises available. Use specific filters to narrow down results."
    
    return result

def format_exercise_detail(exercise: Dict[str, Any]) -> str:
    """Format detailed exercise information with full instructions and GIF"""
    if not exercise:
        return "Exercise not found."
    
    instructions = exercise.get('instructions', [])
    instructions_text = "\n".join([f"{i+1}. {instruction}" for i, instruction in enumerate(instructions)])
    
    secondary_muscles = exercise.get('secondaryMuscles', [])
    secondary_text = ", ".join([muscle.title() for muscle in secondary_muscles]) if secondary_muscles else "None"
    
    gif_section = ""
    if exercise.get('gifUrl'):
        gif_section = f"\n**🎬 Exercise Demonstration (GIF):** {exercise.get('gifUrl')}"
    
    return f"""
**{exercise.get('name', 'Unknown Exercise')}**

**📋 Basic Information:**
- **ID:** {exercise.get('id', 'N/A')}
- **Body Part:** {exercise.get('bodyPart', 'N/A').title()}
- **Primary Target:** {exercise.get('target', 'N/A').title()}
- **Secondary Muscles:** {secondary_text}
- **Equipment:** {exercise.get('equipment', 'N/A').title()}

**📝 Step-by-Step Instructions:**
{instructions_text or 'No detailed instructions available'}
{gif_section}

**ℹ️ Additional Information:**
- **Category:** {exercise.get('category', 'N/A')}
- **Difficulty:** {exercise.get('difficulty', 'N/A')}
"""

def format_workout_plan(exercises: List[Dict[str, Any]], workout_type: str, equipment: str = "various", duration: int = 30) -> str:
    """Format exercises into a structured workout plan with GIFs"""
    if not exercises:
        return "No exercises found for this workout plan."
    
    workout_plan = f"""
# 🏋️ {workout_type.title()} Workout Plan

**⏱️ Duration:** ~{duration} minutes
**🛠️ Equipment:** {equipment.title()}
**💪 Total Exercises:** {len(exercises)}

## 🎯 Workout Structure

"""
    
    for i, exercise in enumerate(exercises, 1):
        instructions = exercise.get('instructions', [])
        main_instruction = instructions[0] if instructions else "Follow proper form and controlled movement"
        
        # Calculate suggested sets/reps based on exercise type
        if "cardio" in exercise.get('bodyPart', '').lower():
            sets_reps = "3 sets of 30-45 seconds"
        elif "abs" in exercise.get('target', '').lower() or "core" in exercise.get('target', '').lower():
            sets_reps = "3 sets of 12-20 reps"
        else:
            sets_reps = "3 sets of 8-12 reps"
        
        gif_section = ""
        if exercise.get('gifUrl'):
            gif_section = f"\n- **🎬 Exercise Demo:** {exercise.get('gifUrl')}"
        
        workout_plan += f"""
### Exercise {i}: {exercise.get('name', 'Unknown Exercise')}
- **🎯 Target:** {exercise.get('target', 'N/A').title()}
- **🛠️ Equipment:** {exercise.get('equipment', 'N/A').title()}
- **📝 Key Instruction:** {main_instruction}
- **📊 Sets/Reps:** {sets_reps}
- **⏰ Rest:** 60-90 seconds between sets{gif_section}

"""
    
    workout_plan += """
## 💡 Workout Guidelines:
- **Warm-up:** 5-10 minutes of light cardio and dynamic stretching
- **Form Focus:** Quality over quantity - maintain proper form throughout
- **Progressive Overload:** Gradually increase intensity as you get stronger
- **Rest Periods:** Allow adequate rest between exercises and sets
- **Cool-down:** 5-10 minutes of stretching and breathing exercises
- **Hydration:** Keep water nearby and stay hydrated
- **Listen to Your Body:** Stop if you feel pain or excessive fatigue

## 🎬 Visual Guides:
All exercises include animated GIF demonstrations to help you maintain proper form and technique.
"""
    
    return workout_plan

@mcp.tool()
async def get_all_exercises(limit: int = 20) -> str:
    """Get a comprehensive list of all exercises in the database with GIF demonstrations. Use limit to control results (max 50 recommended)."""
    endpoint = "/exercises"
    data = await make_api_request(endpoint)
    
    if not data:
        return "❌ Unable to fetch exercises data. Please check your API connection."
    
    return f"**📚 Exercise Database (Showing {min(limit, len(data))} of {len(data)} exercises):**\n\n" + format_exercise_list(data, limit)

@mcp.tool()
async def get_exercise_by_id(exercise_id: str) -> str:
    """Get detailed information about a specific exercise by its ID, including full instructions and GIF demonstration."""
    endpoint = f"/exercises/exercise/{exercise_id}"
    data = await make_api_request(endpoint)
    
    if not data:
        return f"❌ Unable to fetch exercise with ID: {exercise_id}. Please verify the ID is correct."
    
    return format_exercise_detail(data)

@mcp.tool()
async def get_exercises_by_body_part(body_part: str, limit: int = 15) -> str:
    """Get exercises targeting a specific body part with GIF demonstrations. 
    
    Available body parts: back, cardio, chest, lower arms, lower legs, neck, shoulders, upper arms, upper legs, waist"""
    endpoint = f"/exercises/bodyPart/{body_part.lower()}"
    data = await make_api_request(endpoint)
    
    if not data:
        return f"❌ Unable to fetch exercises for body part: {body_part}. Please check the body part name."
    
    return f"**🎯 {body_part.title()} Exercises (Showing {min(limit, len(data))} of {len(data)} exercises):**\n\n" + format_exercise_list(data, limit)

@mcp.tool()
async def get_exercises_by_target_muscle(target_muscle: str, limit: int = 15) -> str:
    """Get exercises targeting a specific muscle with GIF demonstrations.
    
    Popular targets: abs, biceps, calves, chest, glutes, hamstrings, lats, quads, shoulders, triceps, back"""
    endpoint = f"/exercises/target/{target_muscle.lower()}"
    data = await make_api_request(endpoint)
    
    if not data:
        return f"❌ Unable to fetch exercises for target muscle: {target_muscle}. Please check the muscle name."
    
    return f"**🎯 {target_muscle.title()} Targeted Exercises (Showing {min(limit, len(data))} of {len(data)} exercises):**\n\n" + format_exercise_list(data, limit)

@mcp.tool()
async def get_exercises_by_equipment(equipment: str, limit: int = 15) -> str:
    """Get exercises using specific equipment with GIF demonstrations.
    
    Available equipment: barbell, dumbbell, cable, body weight, machine, resistance band, kettlebell, medicine ball, etc."""
    endpoint = f"/exercises/equipment/{equipment.lower().replace(' ', '%20')}"
    data = await make_api_request(endpoint)
    
    if not data:
        return f"❌ Unable to fetch exercises for equipment: {equipment}. Please check the equipment name."
    
    return f"**🛠️ {equipment.title()} Exercises (Showing {min(limit, len(data))} of {len(data)} exercises):**\n\n" + format_exercise_list(data, limit)

@mcp.tool()
async def create_personalized_workout(
    workout_type: str,
    equipment: str = "body weight",
    duration_minutes: int = 30,
    fitness_level: str = "beginner",
    focus_areas: str = "balanced"
) -> str:
    """Create a personalized workout plan with GIF demonstrations for each exercise.
    
    Args:
        workout_type: "chest", "full body", "leg day", "upper body", "cardio", "strength", "hiit"
        equipment: Available equipment ("dumbbell", "barbell", "body weight", "machine", "kettlebell", "any")
        duration_minutes: Target duration (15-60 minutes)
        fitness_level: "beginner", "intermediate", "advanced"
        focus_areas: "strength", "endurance", "muscle building", "fat loss", "balanced"
    """
    
    # Determine exercise count based on duration and fitness level
    if duration_minutes <= 20:
        exercise_count = 4
    elif duration_minutes <= 40:
        exercise_count = 6
    else:
        exercise_count = 8
    
    # Adjust for fitness level
    if fitness_level.lower() == "beginner":
        exercise_count = max(3, exercise_count - 1)
    elif fitness_level.lower() == "advanced":
        exercise_count = min(12, exercise_count + 2)
    
    exercises = []
    
    # Handle different workout types
    if "chest" in workout_type.lower():
        chest_data = await make_api_request(f"/exercises/bodyPart/chest")
        if chest_data:
            if equipment.lower() not in ["any", "all"]:
                chest_data = [ex for ex in chest_data if equipment.lower() in ex.get('equipment', '').lower()]
            exercises.extend(chest_data[:exercise_count])
    
    elif "full body" in workout_type.lower() or "full-body" in workout_type.lower():
        body_parts = ["chest", "back", "upper legs", "shoulders", "upper arms", "waist"]
        exercises_per_part = max(1, exercise_count // len(body_parts))
        
        for body_part in body_parts:
            part_data = await make_api_request(f"/exercises/bodyPart/{body_part}")
            if part_data:
                if equipment.lower() not in ["any", "all"]:
                    part_data = [ex for ex in part_data if equipment.lower() in ex.get('equipment', '').lower()]
                exercises.extend(part_data[:exercises_per_part])
    
    elif "leg" in workout_type.lower() or "lower body" in workout_type.lower():
        upper_legs = await make_api_request(f"/exercises/bodyPart/upper legs")
        lower_legs = await make_api_request(f"/exercises/bodyPart/lower legs")
        
        combined_data = []
        if upper_legs:
            combined_data.extend(upper_legs)
        if lower_legs:
            combined_data.extend(lower_legs)
        
        if combined_data:
            if equipment.lower() not in ["any", "all"]:
                combined_data = [ex for ex in combined_data if equipment.lower() in ex.get('equipment', '').lower()]
            exercises.extend(combined_data[:exercise_count])
    
    elif "upper body" in workout_type.lower():
        upper_parts = ["chest", "back", "shoulders", "upper arms"]
        exercises_per_part = max(1, exercise_count // len(upper_parts))
        
        for body_part in upper_parts:
            part_data = await make_api_request(f"/exercises/bodyPart/{body_part}")
            if part_data:
                if equipment.lower() not in ["any", "all"]:
                    part_data = [ex for ex in part_data if equipment.lower() in ex.get('equipment', '').lower()]
                exercises.extend(part_data[:exercises_per_part])
    
    elif "cardio" in workout_type.lower() or "hiit" in workout_type.lower():
        cardio_data = await make_api_request(f"/exercises/bodyPart/cardio")
        if cardio_data:
            if equipment.lower() not in ["any", "all"]:
                cardio_data = [ex for ex in cardio_data if equipment.lower() in ex.get('equipment', '').lower()]
            exercises.extend(cardio_data[:exercise_count])
    
    else:
        # Try to match with body parts
        body_part_data = await make_api_request(f"/exercises/bodyPart/{workout_type.lower()}")
        if body_part_data:
            if equipment.lower() not in ["any", "all"]:
                body_part_data = [ex for ex in body_part_data if equipment.lower() in ex.get('equipment', '').lower()]
            exercises.extend(body_part_data[:exercise_count])
    
    # If no exercises found, try equipment-based search
    if not exercises and equipment.lower() not in ["any", "all"]:
        equipment_data = await make_api_request(f"/exercises/equipment/{equipment.lower().replace(' ', '%20')}")
        if equipment_data:
            exercises.extend(equipment_data[:exercise_count])
    
    # Remove duplicates and limit to desired count
    seen_ids = set()
    unique_exercises = []
    for exercise in exercises:
        if exercise.get('id') not in seen_ids:
            seen_ids.add(exercise.get('id'))
            unique_exercises.append(exercise)
            if len(unique_exercises) >= exercise_count:
                break
    
    if not unique_exercises:
        return f"❌ Unable to create workout plan for '{workout_type}' with '{equipment}' equipment. Try different parameters."
    
    return format_workout_plan(unique_exercises, workout_type, equipment, duration_minutes)

@mcp.tool()
async def create_circuit_training(
    target_areas: str = "full body",
    equipment: str = "body weight",
    rounds: int = 3,
    exercises_per_round: int = 5,
    work_time: int = 45,
    rest_time: int = 15
) -> str:
    """Create a circuit training workout with multiple rounds and GIF demonstrations.
    
    Args:
        target_areas: "full body", "upper body", "lower body", "core", "cardio"
        equipment: Equipment available
        rounds: Number of circuit rounds
        exercises_per_round: Exercises per round
        work_time: Work duration in seconds
        rest_time: Rest duration in seconds
    """
    
    exercises = []
    
    if "full body" in target_areas.lower():
        body_parts = ["chest", "back", "upper legs", "shoulders", "upper arms", "waist"]
        exercises_per_part = max(1, exercises_per_round // len(body_parts))
        
        for body_part in body_parts:
            part_data = await make_api_request(f"/exercises/bodyPart/{body_part}")
            if part_data:
                if equipment.lower() not in ["any", "all"]:
                    part_data = [ex for ex in part_data if equipment.lower() in ex.get('equipment', '').lower()]
                exercises.extend(part_data[:exercises_per_part])
    
    elif "upper body" in target_areas.lower():
        upper_parts = ["chest", "back", "shoulders", "upper arms"]
        exercises_per_part = max(1, exercises_per_round // len(upper_parts))
        
        for body_part in upper_parts:
            part_data = await make_api_request(f"/exercises/bodyPart/{body_part}")
            if part_data:
                if equipment.lower() not in ["any", "all"]:
                    part_data = [ex for ex in part_data if equipment.lower() in ex.get('equipment', '').lower()]
                exercises.extend(part_data[:exercises_per_part])
    
    elif "lower body" in target_areas.lower():
        lower_parts = ["upper legs", "lower legs"]
        exercises_per_part = max(1, exercises_per_round // len(lower_parts))
        
        for body_part in lower_parts:
            part_data = await make_api_request(f"/exercises/bodyPart/{body_part}")
            if part_data:
                if equipment.lower() not in ["any", "all"]:
                    part_data = [ex for ex in part_data if equipment.lower() in ex.get('equipment', '').lower()]
                exercises.extend(part_data[:exercises_per_part])
    
    elif "core" in target_areas.lower() or "abs" in target_areas.lower():
        core_data = await make_api_request(f"/exercises/bodyPart/waist")
        if core_data:
            if equipment.lower() not in ["any", "all"]:
                core_data = [ex for ex in core_data if equipment.lower() in ex.get('equipment', '').lower()]
            exercises.extend(core_data[:exercises_per_round])
    
    elif "cardio" in target_areas.lower():
        cardio_data = await make_api_request(f"/exercises/bodyPart/cardio")
        if cardio_data:
            if equipment.lower() not in ["any", "all"]:
                cardio_data = [ex for ex in cardio_data if equipment.lower() in ex.get('equipment', '').lower()]
            exercises.extend(cardio_data[:exercises_per_round])
    
    # Remove duplicates and limit to desired count
    seen_ids = set()
    unique_exercises = []
    for exercise in exercises:
        if exercise.get('id') not in seen_ids:
            seen_ids.add(exercise.get('id'))
            unique_exercises.append(exercise)
            if len(unique_exercises) >= exercises_per_round:
                break
    
    if not unique_exercises:
        return f"❌ Unable to create circuit workout for '{target_areas}' with '{equipment}' equipment."
    
    total_time = rounds * (exercises_per_round * work_time + (exercises_per_round - 1) * rest_time + 120)  # Include rest between rounds
    
    circuit_plan = f"""
# 🔥 {target_areas.title()} Circuit Training

**⏱️ Total Duration:** ~{total_time // 60} minutes
**🛠️ Equipment:** {equipment.title()}
**🔄 Rounds:** {rounds}
**💪 Exercises per Round:** {len(unique_exercises)}
**⏰ Work Time:** {work_time} seconds
**😴 Rest Time:** {rest_time} seconds
**🔄 Rest Between Rounds:** 2 minutes

## 🎯 Circuit Structure

"""
    
    for round_num in range(1, rounds + 1):
        circuit_plan += f"### Round {round_num}\n\n"
        
        for i, exercise in enumerate(unique_exercises, 1):
            instructions = exercise.get('instructions', [])
            main_instruction = instructions[0] if instructions else "Maintain proper form throughout"
            
            gif_section = ""
            if exercise.get('gifUrl'):
                gif_section = f"\n- **🎬 Form Guide:** {exercise.get('gifUrl')}"
            
            circuit_plan += f"""
**Exercise {i}: {exercise.get('name', 'Unknown Exercise')}**
- **🎯 Target:** {exercise.get('target', 'N/A').title()}
- **🛠️ Equipment:** {exercise.get('equipment', 'N/A').title()}
- **📝 Focus:** {main_instruction}
- **⏰ Duration:** {work_time} seconds work, {rest_time} seconds rest{gif_section}

"""
        
        if round_num < rounds:
            circuit_plan += "**🔄 Rest 2 minutes before next round**\n\n"
    
    circuit_plan += """
## 💡 Circuit Training Tips:
- **Warm-up:** 5-10 minutes of light movement and dynamic stretching
- **Intensity:** Maintain high intensity during work periods
- **Form Priority:** Never sacrifice form for speed
- **Modifications:** Adjust work/rest ratios based on fitness level
- **Hydration:** Stay hydrated throughout the circuit
- **Cool-down:** 5-10 minutes of stretching and breathing exercises

## 🎬 Visual Demonstrations:
Each exercise includes an animated GIF to help you maintain perfect form and maximize results.
"""
    
    return circuit_plan

@mcp.tool()
async def get_exercise_alternatives(exercise_id: str, limit: int = 5) -> str:
    """Find alternative exercises that target the same muscle groups with GIF demonstrations."""
    # First get the original exercise
    original_exercise = await make_api_request(f"/exercises/exercise/{exercise_id}")
    
    if not original_exercise:
        return f"❌ Unable to find exercise with ID: {exercise_id}"
    
    target_muscle = original_exercise.get('target', '')
    body_part = original_exercise.get('bodyPart', '')
    
    # Get exercises targeting the same muscle
    alternatives = []
    
    if target_muscle:
        target_data = await make_api_request(f"/exercises/target/{target_muscle.lower()}")
        if target_data:
            # Filter out the original exercise
            alternatives = [ex for ex in target_data if ex.get('id') != exercise_id]
    
    if not alternatives and body_part:
        # Fallback to body part if no target alternatives
        bodypart_data = await make_api_request(f"/exercises/bodyPart/{body_part.lower()}")
        if bodypart_data:
            alternatives = [ex for ex in bodypart_data if ex.get('id') != exercise_id]
    
    if not alternatives:
        return f"❌ No alternatives found for exercise ID: {exercise_id}"
    
    result = f"""
**🔄 Alternative Exercises for: {original_exercise.get('name', 'Unknown Exercise')}**
*(Original targets: {target_muscle.title() if target_muscle else 'N/A'} - {body_part.title() if body_part else 'N/A'})*

**📋 Suggested Alternatives:**

""" + format_exercise_list(alternatives, limit)
    
    return result

@mcp.tool()
async def get_beginner_workout_plan(
    focus_area: str = "full body",
    equipment: str = "body weight",
    weeks: int = 4
) -> str:
    """Create a progressive beginner workout plan with GIF demonstrations for each exercise.
    
    Args:
        focus_area: "full body", "upper body", "lower body", "core strength"
        equipment: Available equipment
        weeks: Number of weeks for progression (2-8)
    """
    
    # Get exercises for the focus area
    exercises = []
    
    if "full body" in focus_area.lower():
        body_parts = ["chest", "back", "upper legs", "shoulders", "upper arms", "waist"]
        for body_part in body_parts[:4]:  # Limit to 4 body parts for beginners
            part_data = await make_api_request(f"/exercises/bodyPart/{body_part}")
            if part_data:
                if equipment.lower() not in ["any", "all"]:
                    part_data = [ex for ex in part_data if equipment.lower() in ex.get('equipment', '').lower()]
                exercises.extend(part_data[:2])  # 2 exercises per body part
    
    elif "upper body" in focus_area.lower():
        upper_parts = ["chest", "back", "shoulders", "upper arms"]
        for body_part in upper_parts:
            part_data = await make_api_request(f"/exercises/bodyPart/{body_part}")
            if part_data:
                if equipment.lower() not in ["any", "all"]:
                    part_data = [ex for ex in part_data if equipment.lower() in ex.get('equipment', '').lower()]
                exercises.extend(part_data[:2])
    
    elif "lower body" in focus_area.lower():
        lower_parts = ["upper legs", "lower legs"]
        for body_part in lower_parts:
            part_data = await make_api_request(f"/exercises/bodyPart/{body_part}")
            if part_data:
                if equipment.lower() not in ["any", "all"]:
                    part_data = [ex for ex in part_data if equipment.lower() in ex.get('equipment', '').lower()]
                exercises.extend(part_data[:3])
    
    elif "core" in focus_area.lower():
        core_data = await make_api_request(f"/exercises/bodyPart/waist")
        if core_data:
            if equipment.lower() not in ["any", "all"]:
                core_data = [ex for ex in core_data if equipment.lower() in ex.get('equipment', '').lower()]
            exercises.extend(core_data[:6])
    
    # Remove duplicates
    seen_ids = set()
    unique_exercises = []
    for exercise in exercises:
        if exercise.get('id') not in seen_ids:
            seen_ids.add(exercise.get('id'))
            unique_exercises.append(exercise)
    
    if not unique_exercises:
        return f"❌ Unable to create beginner plan for '{focus_area}' with '{equipment}' equipment."
    
    plan = f"""
# 🌟 Beginner {focus_area.title()} Workout Plan ({weeks} Weeks)

**🎯 Focus:** {focus_area.title()}
**🛠️ Equipment:** {equipment.title()}
**📅 Duration:** {weeks} weeks
**📊 Frequency:** 3 times per week
**⏱️ Session Duration:** 20-30 minutes

## 📈 Progressive Plan Overview

**Week 1-2: Foundation Phase**
- Focus on form and movement patterns
- 2 sets of 8-10 reps for each exercise
- 90-120 seconds rest between sets

**Week 3-4: Building Phase**
- Increase to 3 sets of 10-12 reps
- 60-90 seconds rest between sets
- Add more challenging variations

## 💪 Core Exercises with Visual Guides

"""
    
    for i, exercise in enumerate(unique_exercises[:8], 1):  # Limit to 8 exercises for beginners
        instructions = exercise.get('instructions', [])
        main_instruction = instructions[0] if instructions else "Focus on controlled movement"
        
        gif_section = ""
        if exercise.get('gifUrl'):
            gif_section = f"\n- **🎬 Form Tutorial:** {exercise.get('gifUrl')}"
        
        plan += f"""
### Exercise {i}: {exercise.get('name', 'Unknown Exercise')}
- **🎯 Target:** {exercise.get('target', 'N/A').title()}
- **🛠️ Equipment:** {exercise.get('equipment', 'N/A').title()}
- **📝 Beginner Focus:** {main_instruction}
- **📊 Week 1-2:** 2 sets × 8-10 reps
- **📊 Week 3-4:** 3 sets × 10-12 reps{gif_section}

"""
    
    plan += """
## 🗓️ Sample Weekly Schedule

**Monday:** Full routine
**Tuesday:** Rest or light walking
**Wednesday:** Full routine
**Thursday:** Rest or light stretching
**Friday:** Full routine
**Saturday:** Rest or light activity
**Sunday:** Rest

## 🌟 Beginner Success Tips

1. **Start Slow:** Master the movement before adding intensity
2. **Listen to Your Body:** Some muscle soreness is normal, sharp pain is not
3. **Consistency Over Intensity:** Regular moderate workouts beat sporadic intense ones
4. **Use the GIFs:** Study the visual demonstrations before each exercise
5. **Progress Gradually:** Add weight/reps only when current level feels easy
6. **Rest is Important:** Allow 48 hours between training the same muscle groups
7. **Stay Hydrated:** Drink water before, during, and after workouts
8. **Track Progress:** Keep a simple log of sets, reps, and how you feel

## 🎬 Visual Learning
Each exercise includes an animated GIF demonstration. Study these carefully to:
- Learn proper form and technique
- Understand the full range of motion
- See the exercise pace and rhythm
- Identify common mistakes to avoid
"""
    
    return plan

@mcp.tool()
async def search_exercises_by_name(name: str, limit: int = 10) -> str:
    """Search for exercises by name with GIF demonstrations. Returns exercises that match the search term."""
    endpoint = "/exercises"
    data = await make_api_request(endpoint)
    
    if not data:
        return "❌ Unable to search exercises. Please check your connection."
    
    # Filter exercises by name (case-insensitive)
    search_term = name.lower()
    filtered_exercises = [
        exercise for exercise in data 
        if search_term in exercise.get('name', '').lower()
    ]
    
    if not filtered_exercises:
        return f"❌ No exercises found matching '{name}'. Try different keywords or check spelling."
    
    return f"**🔍 Search Results for '{name}' ({len(filtered_exercises)} found):**\n\n" + format_exercise_list(filtered_exercises, limit)

@mcp.tool()
async def get_workout_by_difficulty(
    difficulty: str = "beginner",
    body_focus: str = "full body",
    equipment: str = "body weight",
    duration: int = 30
) -> str:
    """Create a workout plan tailored to specific difficulty level with GIF demonstrations.
    
    Args:
        difficulty: "beginner", "intermediate", "advanced"
        body_focus: Target body area
        equipment: Available equipment
        duration: Workout duration in minutes
    """
    
    # Adjust exercise count and intensity based on difficulty
    if difficulty.lower() == "beginner":
        exercise_count = 5
        sets_info = "2-3 sets of 8-12 reps"
        rest_info = "90-120 seconds"
        intensity_note = "Focus on learning proper form. Start with bodyweight or light weights."
    elif difficulty.lower() == "intermediate":
        exercise_count = 7
        sets_info = "3-4 sets of 10-15 reps"
        rest_info = "60-90 seconds"
        intensity_note = "Moderate intensity. Challenge yourself while maintaining good form."
    else:  # advanced
        exercise_count = 9
        sets_info = "4-5 sets of 12-20 reps"
        rest_info = "45-75 seconds"
        intensity_note = "High intensity. Push your limits with perfect form and controlled movements."
    
    # Get exercises based on body focus
    exercises = []
    
    if "full body" in body_focus.lower():
        body_parts = ["chest", "back", "upper legs", "shoulders", "upper arms", "waist"]
        exercises_per_part = max(1, exercise_count // len(body_parts))
        
        for body_part in body_parts:
            part_data = await make_api_request(f"/exercises/bodyPart/{body_part}")
            if part_data:
                if equipment.lower() not in ["any", "all"]:
                    part_data = [ex for ex in part_data if equipment.lower() in ex.get('equipment', '').lower()]
                exercises.extend(part_data[:exercises_per_part])
    else:
        # Single body part focus
        part_data = await make_api_request(f"/exercises/bodyPart/{body_focus.lower()}")
        if part_data:
            if equipment.lower() not in ["any", "all"]:
                part_data = [ex for ex in part_data if equipment.lower() in ex.get('equipment', '').lower()]
            exercises.extend(part_data[:exercise_count])
    
    # Remove duplicates and limit
    seen_ids = set()
    unique_exercises = []
    for exercise in exercises:
        if exercise.get('id') not in seen_ids:
            seen_ids.add(exercise.get('id'))
            unique_exercises.append(exercise)
            if len(unique_exercises) >= exercise_count:
                break
    
    if not unique_exercises:
        return f"❌ Unable to create {difficulty} workout for '{body_focus}' with '{equipment}' equipment."
    
    workout_plan = f"""
# 🎯 {difficulty.title()} {body_focus.title()} Workout

**📊 Difficulty Level:** {difficulty.title()}
**🎯 Focus Area:** {body_focus.title()}
**🛠️ Equipment:** {equipment.title()}
**⏱️ Duration:** ~{duration} minutes
**💪 Exercises:** {len(unique_exercises)}

## 📋 {difficulty.title()} Guidelines
- **Sets/Reps:** {sets_info}
- **Rest Between Sets:** {rest_info}
- **Intensity:** {intensity_note}

## 💪 Workout Exercises

"""
    
    for i, exercise in enumerate(unique_exercises, 1):
        instructions = exercise.get('instructions', [])
        main_instruction = instructions[0] if instructions else "Maintain proper form throughout"
        
        gif_section = ""
        if exercise.get('gifUrl'):
            gif_section = f"\n- **🎬 Technique Guide:** {exercise.get('gifUrl')}"
        
        workout_plan += f"""
### Exercise {i}: {exercise.get('name', 'Unknown Exercise')}
- **🎯 Target:** {exercise.get('target', 'N/A').title()}
- **🛠️ Equipment:** {exercise.get('equipment', 'N/A').title()}
- **📝 Key Points:** {main_instruction}
- **📊 {difficulty.title()} Protocol:** {sets_info}
- **⏰ Rest:** {rest_info}{gif_section}

"""
    
    # Add difficulty-specific tips
    if difficulty.lower() == "beginner":
        tips_section = """
## 🌟 Beginner Tips
- Study the GIF demonstrations before starting each exercise
- Start with lighter weights or easier variations
- Focus on learning the movement pattern first
- Don't rush - quality over quantity
- It's okay to take longer rest periods initially
"""
    elif difficulty.lower() == "intermediate":
        tips_section = """
## 🔥 Intermediate Progression
- Use the GIFs to refine your technique
- Gradually increase weight when you can complete all sets easily
- Focus on mind-muscle connection
- Consider adding drop sets or supersets for extra challenge
- Track your progress to ensure continuous improvement
"""
    else:
        tips_section = """
## ⚡ Advanced Techniques
- Use the GIFs to perfect your form even at high intensities
- Implement advanced techniques like rest-pause, drop sets, or tempo work
- Focus on progressive overload and periodization
- Consider adding plyometric or explosive movements
- Push intensity while never compromising form
"""
    
    workout_plan += tips_section + """

## 🎬 Visual Form Guides
Every exercise includes an animated demonstration to help you:
- Master proper technique at your skill level
- Understand the optimal range of motion
- Maintain consistent form throughout your sets
- Progress safely to more advanced variations
"""
    
    return workout_plan

@mcp.tool()
async def get_body_parts_list() -> str:
    """Get a comprehensive list of all available body parts in the database."""
    endpoint = "/exercises/bodyPartList"
    data = await make_api_request(endpoint)
    
    if not data:
        return "❌ Unable to fetch body parts list."
    
    return "**📍 Available Body Parts for Exercise Filtering:**\n\n" + "\n".join([f"• {part.title()}" for part in data])

@mcp.tool()
async def get_target_muscles_list() -> str:
    """Get a comprehensive list of all available target muscles in the database."""
    endpoint = "/exercises/targetList"
    data = await make_api_request(endpoint)
    
    if not data:
        return "❌ Unable to fetch target muscles list."
    
    return "**🎯 Available Target Muscles for Exercise Filtering:**\n\n" + "\n".join([f"• {muscle.title()}" for muscle in data])

@mcp.tool()
async def get_equipment_list() -> str:
    """Get a comprehensive list of all available equipment types in the database."""
    endpoint = "/exercises/equipmentList"
    data = await make_api_request(endpoint)
    
    if not data:
        return "❌ Unable to fetch equipment list."
    
    return "**🛠️ Available Equipment for Exercise Filtering:**\n\n" + "\n".join([f"• {equipment.title()}" for equipment in data])

@mcp.tool()
async def create_hiit_workout(
    intensity: str = "moderate",
    equipment: str = "body weight",
    rounds: int = 4,
    work_time: int = 30,
    rest_time: int = 30
) -> str:
    """Create a High-Intensity Interval Training (HIIT) workout with GIF demonstrations.
    
    Args:
        intensity: "low", "moderate", "high"
        equipment: Available equipment
        rounds: Number of HIIT rounds
        work_time: Work period in seconds
        rest_time: Rest period in seconds
    """
    
    # Get cardio and high-intensity exercises
    cardio_exercises = await make_api_request("/exercises/bodyPart/cardio")
    compound_exercises = []
    
    # Get compound exercises from major muscle groups
    body_parts = ["chest", "back", "upper legs", "shoulders"]
    for body_part in body_parts:
        part_data = await make_api_request(f"/exercises/bodyPart/{body_part}")
        if part_data:
            if equipment.lower() not in ["any", "all"]:
                part_data = [ex for ex in part_data if equipment.lower() in ex.get('equipment', '').lower()]
            compound_exercises.extend(part_data[:2])
    
    # Combine exercises
    all_exercises = []
    if cardio_exercises:
        if equipment.lower() not in ["any", "all"]:
            cardio_exercises = [ex for ex in cardio_exercises if equipment.lower() in ex.get('equipment', '').lower()]
        all_exercises.extend(cardio_exercises[:3])
    
    all_exercises.extend(compound_exercises)
    
    # Remove duplicates
    seen_ids = set()
    unique_exercises = []
    for exercise in all_exercises:
        if exercise.get('id') not in seen_ids:
            seen_ids.add(exercise.get('id'))
            unique_exercises.append(exercise)
            if len(unique_exercises) >= 6:  # Limit for HIIT
                break
    
    if not unique_exercises:
        return f"❌ Unable to create HIIT workout with '{equipment}' equipment."
    
    total_time = rounds * (len(unique_exercises) * (work_time + rest_time))
    
    hiit_plan = f"""
# 🔥 HIIT Workout - {intensity.title()} Intensity

**⚡ Intensity Level:** {intensity.title()}
**🛠️ Equipment:** {equipment.title()}
**🔄 Rounds:** {rounds}
**💪 Exercises:** {len(unique_exercises)}
**⏰ Work Time:** {work_time} seconds
**😴 Rest Time:** {rest_time} seconds
**⏱️ Total Time:** ~{total_time // 60} minutes

## 🎯 HIIT Structure

Perform each exercise for {work_time} seconds, rest for {rest_time} seconds, then move to the next exercise. Complete all exercises for one round, then repeat for {rounds} total rounds.

"""
    
    for round_num in range(1, rounds + 1):
        hiit_plan += f"### Round {round_num}\n\n"
        
        for i, exercise in enumerate(unique_exercises, 1):
            instructions = exercise.get('instructions', [])
            main_instruction = instructions[0] if instructions else "Maintain high intensity"
            
            gif_section = ""
            if exercise.get('gifUrl'):
                gif_section = f"\n- **🎬 Form Demo:** {exercise.get('gifUrl')}"
            
            hiit_plan += f"""
**Exercise {i}: {exercise.get('name', 'Unknown Exercise')}**
- **🎯 Target:** {exercise.get('target', 'N/A').title()}
- **🛠️ Equipment:** {exercise.get('equipment', 'N/A').title()}
- **📝 HIIT Focus:** {main_instruction}
- **⏰ Duration:** {work_time}s work → {rest_time}s rest{gif_section}

"""
        
        if round_num < rounds:
            hiit_plan += "**🔄 Complete rest, then start next round**\n\n"
    
    # Intensity-specific guidelines
    if intensity.lower() == "low":
        intensity_guide = """
## 🌱 Low Intensity Guidelines
- Work at 60-70% of maximum effort
- Focus on maintaining good form throughout
- This is great for beginners or recovery days
- You should be able to maintain a conversation during rest periods
"""
    elif intensity.lower() == "moderate":
        intensity_guide = """
## 🔥 Moderate Intensity Guidelines
- Work at 70-85% of maximum effort
- Push yourself but maintain control
- You should feel challenged but not completely exhausted
- Brief conversations possible during rest periods
"""
    else:
        intensity_guide = """
## ⚡ High Intensity Guidelines
- Work at 85-95% of maximum effort
- Give everything you have during work periods
- You should feel significantly challenged
- Focus on recovery during rest periods - minimal talking
"""
    
    hiit_plan += intensity_guide + """

## 💡 HIIT Success Tips
- **Warm-up:** 5-10 minutes of light cardio and dynamic stretching
- **Form First:** Never sacrifice form for speed, even in HIIT
- **Use the GIFs:** Study proper technique before starting
- **Listen to Your Body:** Adjust intensity based on how you feel
- **Stay Hydrated:** Keep water nearby throughout the workout
- **Cool-down:** 5-10 minutes of walking and stretching

## 🎬 Visual Technique Guides
Each exercise includes animated demonstrations to help you maintain proper form even at high intensity.
"""
    
    return hiit_plan

@mcp.tool()
async def get_exercise_modifications(exercise_id: str) -> str:
    """Get easier and harder modifications for a specific exercise with GIF demonstrations."""
    # Get the original exercise
    original_exercise = await make_api_request(f"/exercises/exercise/{exercise_id}")
    
    if not original_exercise:
        return f"❌ Unable to find exercise with ID: {exercise_id}"
    
    target_muscle = original_exercise.get('target', '')
    equipment = original_exercise.get('equipment', '')
    
    # Find related exercises that could be modifications
    related_exercises = []
    
    if target_muscle:
        target_data = await make_api_request(f"/exercises/target/{target_muscle.lower()}")
        if target_data:
            related_exercises = [ex for ex in target_data if ex.get('id') != exercise_id]
    
    # Separate by equipment complexity for easier/harder suggestions
    bodyweight_exercises = [ex for ex in related_exercises if 'body weight' in ex.get('equipment', '').lower()]
    equipment_exercises = [ex for ex in related_exercises if 'body weight' not in ex.get('equipment', '').lower()]
    
    result = f"""
**🔧 Exercise Modifications for: {original_exercise.get('name', 'Unknown Exercise')}**

**📋 Original Exercise Details:**
- **Target:** {target_muscle.title() if target_muscle else 'N/A'}
- **Equipment:** {equipment.title() if equipment else 'N/A'}
- **🎬 Original Demo:** {original_exercise.get('gifUrl', 'N/A')}

## 🌱 Easier Modifications (Beginner-Friendly)

"""
    
    # Show easier alternatives (typically bodyweight)
    if bodyweight_exercises:
        easier_exercises = bodyweight_exercises[:3]
        for i, exercise in enumerate(easier_exercises, 1):
            gif_section = ""
            if exercise.get('gifUrl'):
                gif_section = f"\n- **🎬 Demo:** {exercise.get('gifUrl')}"
            
            result += f"""
**{i}. {exercise.get('name', 'Unknown Exercise')}**
- **Equipment:** {exercise.get('equipment', 'N/A').title()}
- **Why Easier:** Requires less equipment and resistance
- **Instructions:** {exercise.get('instructions', ['No instructions available'])[0][:100] if exercise.get('instructions') else 'Focus on proper form'}{gif_section}

"""
    else:
        result += "No easier bodyweight alternatives found for this exercise.\n\n"
    
    result += "## ⚡ Harder Modifications (Advanced Challenges)\n\n"
    
    # Show harder alternatives (typically with equipment)
    if equipment_exercises:
        harder_exercises = equipment_exercises[:3]
        for i, exercise in enumerate(harder_exercises, 1):
            gif_section = ""
            if exercise.get('gifUrl'):
                gif_section = f"\n- **🎬 Demo:** {exercise.get('gifUrl')}"
            
            result += f"""
**{i}. {exercise.get('name', 'Unknown Exercise')}**
- **Equipment:** {exercise.get('equipment', 'N/A').title()}
- **Why Harder:** Requires additional equipment or resistance
- **Instructions:** {exercise.get('instructions', ['No instructions available'])[0][:100] if exercise.get('instructions') else 'Focus on controlled movement'}{gif_section}

"""
    else:
        result += "No harder equipment-based alternatives found.\n\n"
    
    result += """
## 💡 Modification Tips
- **Progression:** Start with easier versions and gradually work up
- **Listen to Your Body:** Choose modifications based on your current ability
- **Form Priority:** Perfect easier versions before attempting harder ones
- **Use GIFs:** Study the demonstrations to understand proper technique
- **Consistency:** Regular practice with appropriate modifications beats sporadic advanced attempts
"""
    
    return result

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')