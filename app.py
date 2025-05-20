import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

# Use SQLite for the temporary preview
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posh_nosh.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define models directly in this file for simplicity
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with client profiles
    profile = db.relationship('ClientProfile', backref='user', uselist=False)
    
    # Relationship with meal selections
    meal_selections = db.relationship('MealSelection', backref='user')
    
    # Relationship with feedback
    feedback = db.relationship('Feedback', backref='user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class ClientProfile(db.Model):
    __tablename__ = 'client_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Dietary information
    allergies = db.Column(db.Text)
    dietary_restrictions = db.Column(db.Text)
    medical_conditions = db.Column(db.Text)
    
    # Food preferences
    favorite_cuisines = db.Column(db.Text)
    disliked_ingredients = db.Column(db.Text)
    spice_tolerance = db.Column(db.String(20))
    texture_preferences = db.Column(db.Text)
    protein_preferences = db.Column(db.Text)
    vegetable_preferences = db.Column(db.Text)
    carb_preferences = db.Column(db.Text)
    
    # Service preferences
    package_type = db.Column(db.String(50))
    servings_per_meal = db.Column(db.Integer)
    meal_distribution = db.Column(db.Text)
    packaging_preference = db.Column(db.String(50))
    dietary_goals = db.Column(db.Text)
    
    # Scheduling
    preferred_day = db.Column(db.String(20))
    preferred_time = db.Column(db.String(50))
    service_frequency = db.Column(db.String(20))
    
    # Kitchen information
    kitchen_equipment = db.Column(db.Text)
    storage_preferences = db.Column(db.Text)
    kitchen_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ClientProfile {self.id}>'


class Menu(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)  # breakfast, lunch, dinner, snack
    image_url = db.Column(db.String(255))
    dietary_tags = db.Column(db.String(255))  # comma-separated tags like "vegan,gluten-free"
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with meal selections
    selections = db.relationship('MealSelection', backref='menu_item')
    
    def __repr__(self):
        return f'<Menu {self.name}>'


class MealSelection(db.Model):
    __tablename__ = 'meal_selections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    week_of = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    special_instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MealSelection {self.id}>'


class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meal_selection_id = db.Column(db.Integer, db.ForeignKey('meal_selections.id'), nullable=False)
    rating = db.Column(db.Integer)  # 1-5 star rating
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with meal selections
    meal_selection = db.relationship('MealSelection', backref='feedback')
    
    def __repr__(self):
        return f'<Feedback {self.id}>'


class Package(db.Model):
    __tablename__ = 'packages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    meals_count = db.Column(db.Integer)
    servings_per_meal = db.Column(db.Integer)
    service_fee = db.Column(db.Float)
    is_all_inclusive = db.Column(db.Boolean, default=False)
    all_inclusive_price = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Package {self.name}>'

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html', title="About Us")

@app.route('/services')
def services():
    packages = Package.query.filter_by(is_active=True).all()
    return render_template('services.html', title="Our Services", packages=packages)

@app.route('/contact')
def contact():
    return render_template('contact.html', title="Contact Us")

# Auth routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html', title="Login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Validate form data
        if not email or not password or not confirm_password or not first_name or not last_name:
            flash('All required fields must be filled.', 'danger')
            return render_template('register.html', title="Register")
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', title="Register")
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login or use a different email.', 'danger')
            return render_template('register.html', title="Register")
        
        # Create new user
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address=address
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title="Register")

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Client routes
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access this page.', 'warning')
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    
    # Get upcoming meal selections
    upcoming_selections = MealSelection.query.filter_by(user_id=user.id).order_by(MealSelection.week_of.desc()).limit(5).all()
    
    # Check if profile is complete
    profile_complete = user.profile is not None
    
    return render_template('dashboard.html', 
                          title="Dashboard",
                          user=user, 
                          upcoming_selections=upcoming_selections,
                          profile_complete=profile_complete)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please login to access this page.', 'warning')
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    profile = user.profile
    
    if request.method == 'POST':
        # Update user information
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        user.address = request.form.get('address')
        
        # Create or update profile
        if not profile:
            profile = ClientProfile(user_id=user.id)
            db.session.add(profile)
        
        # Update dietary information
        profile.allergies = request.form.get('allergies')
        profile.dietary_restrictions = request.form.get('dietary_restrictions')
        profile.medical_conditions = request.form.get('medical_conditions')
        
        # Update food preferences
        profile.favorite_cuisines = request.form.get('favorite_cuisines')
        profile.disliked_ingredients = request.form.get('disliked_ingredients')
        profile.spice_tolerance = request.form.get('spice_tolerance')
        profile.texture_preferences = request.form.get('texture_preferences')
        profile.protein_preferences = request.form.get('protein_preferences')
        profile.vegetable_preferences = request.form.get('vegetable_preferences')
        profile.carb_preferences = request.form.get('carb_preferences')
        
        # Update service preferences
        profile.package_type = request.form.get('package_type')
        profile.servings_per_meal = request.form.get('servings_per_meal')
        profile.meal_distribution = request.form.get('meal_distribution')
        profile.packaging_preference = request.form.get('packaging_preference')
        profile.dietary_goals = request.form.get('dietary_goals')
        
        # Update scheduling
        profile.preferred_day = request.form.get('preferred_day')
        profile.preferred_time = request.form.get('preferred_time')
        profile.service_frequency = request.form.get('service_frequency')
        
        # Update kitchen information
        profile.kitchen_equipment = request.form.get('kitchen_equipment')
        profile.storage_preferences = request.form.get('storage_preferences')
        profile.kitchen_notes = request.form.get('kitchen_notes')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get all packages for the form
    packages = Package.query.filter_by(is_active=True).all()
    
    return render_template('profile.html', 
                          title="My Profile",
                          user=user, 
                          profile=profile, 
                          packages=packages)

@app.route('/menu')
def menu():
    # Get all menu items grouped by category
    breakfast_items = Menu.query.filter_by(category='breakfast', is_active=True).all()
    lunch_items = Menu.query.filter_by(category='lunch', is_active=True).all()
    dinner_items = Menu.query.filter_by(category='dinner', is_active=True).all()
    snack_items = Menu.query.filter_by(category='snack', is_active=True).all()
    
    return render_template('menu.html',
                          title="Our Menu",
                          breakfast_items=breakfast_items,
                          lunch_items=lunch_items,
                          dinner_items=dinner_items,
                          snack_items=snack_items)

# Create database tables and seed data
# Flask 3.x doesn't support before_first_request, using with app.app_context() instead
with app.app_context():
    db.create_all()
    
    # Check if we need to seed initial data
    if Package.query.count() == 0:
        # Seed package data
        starter = Package(
            name="Starter Package",
            description="3 meals per week (4 servings each)",
            meals_count=3,
            servings_per_meal=4,
            service_fee=325.00,
            is_all_inclusive=False
        )
        
        standard = Package(
            name="Standard Package",
            description="5 meals per week (4 servings each)",
            meals_count=5,
            servings_per_meal=4,
            service_fee=450.00,
            is_all_inclusive=False
        )
        
        premium = Package(
            name="Premium Package",
            description="5 meals plus brunch/snack prep (4 servings each)",
            meals_count=5,
            servings_per_meal=4,
            service_fee=575.00,
            is_all_inclusive=False
        )
        
        all_inclusive = Package(
            name="All-Inclusive Premium",
            description="5 meals per week (4 servings each), includes all ingredients and packaging",
            meals_count=5,
            servings_per_meal=4,
            service_fee=0.00,
            is_all_inclusive=True,
            all_inclusive_price=800.00
        )
        
        db.session.add_all([starter, standard, premium, all_inclusive])
        db.session.commit()
    
    # Seed menu items if needed
    if Menu.query.count() == 0:
        # Breakfast items
        breakfast_items = [
            Menu(name="Chia oat parfaits with berry compote", description="Nutrient-rich chia seeds and rolled oats layered with Greek yogurt and homemade berry compote", category="breakfast", dietary_tags="vegetarian"),
            Menu(name="Sweet potato frittata slices", description="Savory egg frittata with roasted sweet potatoes, spinach, and goat cheese", category="breakfast", dietary_tags="vegetarian,gluten-free"),
            Menu(name="Overnight oats with seasonal fruits", description="Steel-cut oats soaked overnight with almond milk, topped with seasonal fruits and honey", category="breakfast", dietary_tags="vegetarian"),
            Menu(name="Protein-packed breakfast burritos", description="Whole wheat tortillas filled with scrambled eggs, black beans, avocado, and salsa", category="breakfast", dietary_tags="vegetarian")
        ]
        
        # Lunch items
        lunch_items = [
            Menu(name="Moroccan chickpea bowls with tahini drizzle", description="Spiced chickpeas with roasted vegetables, quinoa, and homemade tahini sauce", category="lunch", dietary_tags="vegan,gluten-free"),
            Menu(name="Grilled chicken with quinoa tabbouleh", description="Herb-marinated grilled chicken breast served with refreshing quinoa tabbouleh", category="lunch", dietary_tags="gluten-free"),
            Menu(name="Sesame-crusted ahi tuna salad", description="Seared sesame-crusted ahi tuna over mixed greens with ginger-miso dressing", category="lunch", dietary_tags="gluten-free"),
            Menu(name="Mediterranean vegetable wraps", description="Grilled vegetables, hummus, and feta cheese wrapped in whole grain lavash", category="lunch", dietary_tags="vegetarian")
        ]
        
        # Dinner items
        dinner_items = [
            Menu(name="Miso-glazed salmon with soba noodles", description="Wild-caught salmon with miso glaze, served with buckwheat soba noodles and sesame vegetables", category="dinner", dietary_tags=""),
            Menu(name="Thai green curry with tofu & vegetables", description="Aromatic Thai green curry with firm tofu, seasonal vegetables, and jasmine rice", category="dinner", dietary_tags="vegan,gluten-free"),
            Menu(name="Herb-roasted chicken with seasonal vegetables", description="Free-range chicken roasted with fresh herbs, served with seasonal roasted vegetables", category="dinner", dietary_tags="gluten-free"),
            Menu(name="Wild mushroom risotto", description="Creamy Arborio rice slowly cooked with assorted wild mushrooms and finished with Parmesan", category="dinner", dietary_tags="vegetarian,gluten-free")
        ]
        
        # Snack items
        snack_items = [
            Menu(name="Wholesome energy bites", description="No-bake energy bites made with oats, nut butter, honey, and dark chocolate", category="snack", dietary_tags="vegetarian"),
            Menu(name="Hummus & veggie packs", description="House-made hummus with fresh-cut vegetables for dipping", category="snack", dietary_tags="vegan,gluten-free"),
            Menu(name="Greek yogurt parfaits", description="Greek yogurt layered with house-made granola and fresh berries", category="snack", dietary_tags="vegetarian"),
            Menu(name="Spiced nuts and dried fruits", description="Assorted nuts roasted with herbs and spices, mixed with premium dried fruits", category="snack", dietary_tags="vegan,gluten-free")
        ]
        
        all_items = breakfast_items + lunch_items + dinner_items + snack_items
        db.session.add_all(all_items)
        db.session.commit()
        
        # Create a demo user
        if User.query.count() == 0:
            demo_user = User(
                email="demo@poshnoshservices.ca",
                first_name="Demo",
                last_name="User",
                phone="(604) 555-1234",
                address="123 Main St, Vancouver, BC"
            )
            demo_user.set_password("demopassword")
            db.session.add(demo_user)
            db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
