# Creating a Signup Wizard with Frappe Studio (Visual Builder)

Frappe Studio is a visual app builder that lets you create forms and pages without writing code. Here's how to build your signup wizard using Studio.

## Prerequisites

1. **Ensure Studio is installed and running:**
   ```bash
   cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
   bench get-app studio  # If not already installed
   bench --site koraflow-site install-app studio
   ```

2. **Access Studio:**
   - Navigate to: `http://localhost:8000/studio` (or your site URL + `/studio`)
   - Login as Administrator

## Step 1: Create the Custom DocType (Still Required)

Even with Studio, you need to create the DocType first. You can do this via:

**Option A: Via Desk UI**
1. Go to **Desk** → **Customize** → **DocType** → **New**
2. Name it: `Signup Data`
3. Add your fields (see `SIGNUP_WIZARD_IMPLEMENTATION.md` for field structure)

**Option B: Via Studio (if supported)**
- Studio may have DocType creation features in future versions

## Step 2: Create a New Studio Page

1. **Open Studio:**
   - Go to `/studio` in your browser
   - Click **"New App"** or select an existing app

2. **Create a New Page:**
   - Click **"New Page"** or **"+"** button
   - Name it: `Signup Wizard`
   - This creates a `Studio Page` record

## Step 3: Build the Wizard Steps Visually

### Step 3.1: Create Step 1 - Personal Information

1. **Add a Container/Layout Component:**
   - Drag a **Container** or **Card** component onto the canvas
   - This will hold your first step

2. **Add Form Fields:**
   - Drag **TextInput** components for:
     - First Name
     - Last Name
     - Email
     - Phone
   - Configure each field:
     - Right-click → **Edit Properties**
     - Set `label`, `placeholder`, `required`, etc.
     - Bind to a variable (e.g., `signupData.firstName`)

3. **Add Navigation Buttons:**
   - Drag a **Button** component
   - Label: "Next"
   - Add click event handler (see Step 4)

### Step 3.2: Create Step 2 - Company Details

1. **Add Another Container:**
   - This will be your second step
   - Initially hide it (use conditional rendering)

2. **Add Fields:**
   - Company Name (TextInput)
   - Company Size (Select/Dropdown)
   - Industry (Select/Dropdown)

3. **Add Navigation:**
   - "Back" button
   - "Next" button

### Step 3.3: Create Step 3 - Preferences

1. **Add Final Container:**
   - Use Case (TextArea)
   - How did you hear about us? (Select)
   - Newsletter Subscribe (Checkbox)

2. **Add Submit Button:**
   - "Complete Signup" button

## Step 4: Add Variables and Logic

### Create Variables

1. **Open Variables Panel:**
   - In Studio, find the **Variables** section
   - Click **"Add Variable"**

2. **Create Required Variables:**
   ```javascript
   // In Studio Variables panel
   currentStep: 0
   signupData: {
     firstName: '',
     lastName: '',
     email: '',
     phone: '',
     companyName: '',
     companySize: '',
     industry: '',
     useCase: '',
     hearAboutUs: '',
     newsletterSubscribe: false
   }
   ```

### Add Watchers (Conditional Display)

1. **Show/Hide Steps Based on currentStep:**
   - Select Step 1 Container
   - Add condition: `currentStep === 0`
   - Select Step 2 Container
   - Add condition: `currentStep === 1`
   - Select Step 3 Container
   - Add condition: `currentStep === 2`

## Step 5: Add Event Handlers

### Next Button Handler

1. **Select the "Next" Button**
2. **Add Click Event:**
   - Open **Events** panel
   - Add `@click` handler
   - Add script:
   ```javascript
   // Validate current step
   if (currentStep === 0) {
     if (!signupData.firstName || !signupData.lastName || !signupData.email) {
       frappe.msgprint('Please fill all required fields');
       return;
     }
   }
   
   // Move to next step
   if (currentStep < 2) {
     currentStep++;
   } else {
     // Complete signup
     completeSignup();
   }
   ```

### Back Button Handler

```javascript
if (currentStep > 0) {
  currentStep--;
}
```

### Complete Signup Function

Add this in the **Scripts** section of Studio:

```javascript
async function completeSignup() {
  try {
    const result = await frappe.call({
      method: 'koraflow_core.api.signup.complete_signup',
      args: {
        signup_id: frappe.session.get('signup_id')
      }
    });
    
    if (result.message.success) {
      frappe.msgprint({
        title: 'Success',
        message: 'Signup completed! Please check your email.',
        indicator: 'green'
      });
      window.location.href = '/';
    }
  } catch (error) {
    frappe.msgprint({
      title: 'Error',
      message: error.message,
      indicator: 'red'
    });
  }
}
```

## Step 6: Add Progress Indicator

1. **Add a Progress Component:**
   - Drag a **Progress** or custom component
   - Or create a visual indicator using multiple divs/circles

2. **Bind to currentStep:**
   - Use `currentStep` variable to highlight active step
   - Example: `:class="{ active: currentStep >= 0 }"` for step 1

## Step 7: Connect to Data Source

1. **Add Data Source:**
   - In Studio, find **Resources** panel
   - Add a new resource pointing to your DocType: `Signup Data`

2. **Bind Form Fields:**
   - Connect each input field to the data source
   - Use Studio's data binding interface

## Step 8: Save and Test

1. **Save Your Page:**
   - Click **Save** in Studio
   - The page is saved as a `Studio Page` record

2. **Access Your Wizard:**
   - Studio pages are accessible at: `/studio-apps/[app-name]/[page-name]`
   - Or configure a custom route in Studio settings

## Alternative: Using Studio's Form Utilities

Studio has form utilities that can help:

1. **Form Dialog Component:**
   - Use Studio's built-in form components
   - These automatically handle data binding

2. **CRUD Utilities:**
   - Studio provides CRUD operations
   - Can auto-generate forms from DocTypes

## Tips for Multi-Step Wizards in Studio

1. **Use Conditional Rendering:**
   - Show/hide steps based on `currentStep` variable
   - Use Studio's conditional display features

2. **State Management:**
   - Store form data in variables
   - Use Studio's variable system for state

3. **Validation:**
   - Add validation in event handlers
   - Use Studio's validation features if available

4. **Styling:**
   - Use Studio's style editor
   - Apply custom CSS if needed

## Limitations & Workarounds

**Current Studio Limitations:**
- Multi-step wizards may require custom JavaScript
- Complex state management might need code
- Some advanced features may not be fully visual

**Workarounds:**
- Use Studio for layout and basic structure
- Add custom scripts in Studio's Script section
- Combine visual building with minimal code

## Next Steps

1. **Start with Studio:**
   - Create the basic layout visually
   - Add form fields using drag-and-drop

2. **Add Logic:**
   - Use Studio's script section for step navigation
   - Add API calls for saving data

3. **Test Iteratively:**
   - Test each step as you build
   - Refine based on user feedback

## Resources

- **Studio Documentation:** Check `/studio` for built-in help
- **Studio GitHub:** https://github.com/frappe/studio
- **Frappe UI Components:** Available in Studio's component library

## Getting Help from Ollama

You can still use Ollama to get guidance on Studio-specific questions:

```python
from llm_service.ollama_client import OllamaClient

client = OllamaClient(config={
    'ollama': {
        'host': 'localhost',
        'port': 11434,
        'model': 'llama3'
    }
})

response = client.generate(
    prompt="""
    How do I create a multi-step form in Frappe Studio?
    I need to:
    - Show/hide different steps
    - Navigate between steps
    - Save data at each step
    - Use Studio's visual builder
    
    Provide Studio-specific guidance.
    """,
    temperature=0.7
)
print(response)
```





