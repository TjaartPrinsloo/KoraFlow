# Signup Wizard Implementation Guide

This guide shows you how to create a multi-step signup wizard similar to the onboarding wizard, with custom fields for user registration.

## Step 1: Ask Ollama for Guidance

First, use Ollama to get AI-powered guidance on your specific requirements:

```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow
python3 scripts/ask_ollama_wizard_guide.py
```

Or call Ollama directly:

```python
from llm_service.ollama_client import OllamaClient

client = OllamaClient()
response = client.generate(
    prompt="Guide me on creating a signup wizard with steps: 1) Personal Info, 2) Company Details, 3) Preferences. Include custom fields like company_size, industry, use_case.",
    temperature=0.7
)
print(response)
```

## Step 2: Create Custom DocType for Signup Data

Create a DocType to store the signup information:

**File: `apps/koraflow_core/koraflow_core/doctype/signup_data/signup_data.json`**

```json
{
 "actions": [],
 "allow_rename": 1,
 "autoname": "hash",
 "creation": "2024-01-01 00:00:00.000000",
 "doctype": "DocType",
 "editable_grid": 1,
 "engine": "InnoDB",
 "field_order": [
  "section_personal",
  "first_name",
  "last_name",
  "email",
  "phone",
  "column_break_1",
  "company_name",
  "company_size",
  "industry",
  "section_preferences",
  "use_case",
  "hear_about_us",
  "newsletter_subscribe"
 ],
 "fields": [
  {
   "fieldname": "section_personal",
   "fieldtype": "Section Break",
   "label": "Personal Information"
  },
  {
   "fieldname": "first_name",
   "fieldtype": "Data",
   "label": "First Name",
   "reqd": 1
  },
  {
   "fieldname": "last_name",
   "fieldtype": "Data",
   "label": "Last Name",
   "reqd": 1
  },
  {
   "fieldname": "email",
   "fieldtype": "Data",
   "label": "Email",
   "options": "Email",
   "reqd": 1,
   "unique": 1
  },
  {
   "fieldname": "phone",
   "fieldtype": "Data",
   "label": "Phone Number"
  },
  {
   "fieldname": "column_break_1",
   "fieldtype": "Column Break"
  },
  {
   "fieldname": "company_name",
   "fieldtype": "Data",
   "label": "Company Name"
  },
  {
   "fieldname": "company_size",
   "fieldtype": "Select",
   "label": "Company Size",
   "options": "1-10\n11-50\n51-200\n201-500\n500+"
  },
  {
   "fieldname": "industry",
   "fieldtype": "Select",
   "label": "Industry",
   "options": "Technology\nManufacturing\nRetail\nHealthcare\nFinance\nOther"
  },
  {
   "fieldname": "section_preferences",
   "fieldtype": "Section Break",
   "label": "Preferences"
  },
  {
   "fieldname": "use_case",
   "fieldtype": "Small Text",
   "label": "How do you plan to use KoraFlow?"
  },
  {
   "fieldname": "hear_about_us",
   "fieldtype": "Select",
   "label": "How did you hear about us?",
   "options": "Google Search\nSocial Media\nReferral\nConference\nOther"
  },
  {
   "default": 0,
   "fieldname": "newsletter_subscribe",
   "fieldtype": "Check",
   "label": "Subscribe to Newsletter"
  }
 ],
 "index_web_pages_for_search": 1,
 "issingle": 0,
 "module": "Core",
 "name": "Signup Data",
 "owner": "Administrator",
 "permissions": [
  {
   "create": 1,
   "delete": 1,
   "email": 1,
   "read": 1,
   "role": "System Manager",
   "write": 1
  },
  {
   "create": 1,
   "read": 1,
   "role": "Guest",
   "write": 1
  }
 ],
 "sort_field": "creation",
 "sort_order": "DESC"
}
```

## Step 3: Create Python API Methods

**File: `apps/koraflow_core/koraflow_core/api/signup.py`**

```python
import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def save_signup_step(step, data):
    """Save data for a specific step of the signup wizard"""
    try:
        # Get or create signup data record
        # In a real implementation, you'd use session or temporary storage
        signup_id = frappe.session.get('signup_id')
        
        if not signup_id:
            # Create new signup data record
            doc = frappe.get_doc({
                "doctype": "Signup Data",
                **data
            })
            doc.insert(ignore_permissions=True)
            signup_id = doc.name
            frappe.session['signup_id'] = signup_id
        else:
            # Update existing record
            doc = frappe.get_doc("Signup Data", signup_id)
            doc.update(data)
            doc.save(ignore_permissions=True)
        
        frappe.db.commit()
        
        return {
            "success": True,
            "signup_id": signup_id,
            "message": _("Step {0} saved successfully").format(step)
        }
    except Exception as e:
        frappe.log_error(f"Signup step save error: {str(e)}")
        return {
            "success": False,
            "message": _("Error saving step: {0}").format(str(e))
        }

@frappe.whitelist(allow_guest=True)
def complete_signup(signup_id):
    """Complete the signup process and create user"""
    try:
        signup_data = frappe.get_doc("Signup Data", signup_id)
        
        # Create user account
        user = frappe.get_doc({
            "doctype": "User",
            "email": signup_data.email,
            "first_name": signup_data.first_name,
            "last_name": signup_data.last_name,
            "phone": signup_data.phone,
            "user_type": "Website User",
            "send_welcome_email": 1
        })
        user.insert(ignore_permissions=True)
        
        # Add default role
        default_role = frappe.get_single_value("Portal Settings", "default_role")
        if default_role:
            user.add_roles(default_role)
        
        # Mark signup as complete
        signup_data.status = "Completed"
        signup_data.user = user.name
        signup_data.save(ignore_permissions=True)
        
        frappe.db.commit()
        
        return {
            "success": True,
            "user": user.name,
            "message": _("Signup completed successfully")
        }
    except Exception as e:
        frappe.log_error(f"Signup completion error: {str(e)}")
        return {
            "success": False,
            "message": _("Error completing signup: {0}").format(str(e))
        }
```

## Step 4: Create Vue.js Wizard Component

**File: `apps/koraflow_core/koraflow_core/www/signup_wizard.js`**

```javascript
// Multi-step signup wizard component
frappe.provide("koraflow.signup");

koraflow.signup.Wizard = class {
    constructor(element) {
        this.element = element;
        this.currentStep = 0;
        this.steps = [
            {
                title: "Personal Information",
                component: "PersonalInfoStep",
                fields: ["first_name", "last_name", "email", "phone"]
            },
            {
                title: "Company Details",
                component: "CompanyDetailsStep",
                fields: ["company_name", "company_size", "industry"]
            },
            {
                title: "Preferences",
                component: "PreferencesStep",
                fields: ["use_case", "hear_about_us", "newsletter_subscribe"]
            }
        ];
        this.data = {};
        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
    }

    render() {
        const step = this.steps[this.currentStep];
        this.element.html(`
            <div class="signup-wizard">
                <div class="wizard-progress">
                    ${this.steps.map((s, i) => `
                        <div class="progress-step ${i <= this.currentStep ? 'active' : ''}">
                            <div class="step-number">${i + 1}</div>
                            <div class="step-title">${s.title}</div>
                        </div>
                    `).join('')}
                </div>
                <div class="wizard-content">
                    <h2>${step.title}</h2>
                    <div class="wizard-form" data-step="${this.currentStep}">
                        ${this.renderStepForm(step)}
                    </div>
                    <div class="wizard-actions">
                        ${this.currentStep > 0 ? '<button class="btn btn-secondary" onclick="wizard.prev()">Back</button>' : ''}
                        <button class="btn btn-primary" onclick="wizard.next()">
                            ${this.currentStep === this.steps.length - 1 ? 'Complete Signup' : 'Next'}
                        </button>
                    </div>
                </div>
            </div>
        `);
    }

    renderStepForm(step) {
        // Render form fields based on step
        // This would dynamically create form inputs
        return `<div>Form fields for ${step.title}</div>`;
    }

    async next() {
        // Validate current step
        if (!this.validateStep(this.currentStep)) {
            return;
        }

        // Save current step data
        await this.saveStep();

        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            this.render();
        } else {
            await this.completeSignup();
        }
    }

    prev() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.render();
        }
    }

    validateStep(stepIndex) {
        const step = this.steps[stepIndex];
        // Validate required fields
        return true;
    }

    async saveStep() {
        const step = this.steps[this.currentStep];
        const stepData = {};
        
        step.fields.forEach(field => {
            const input = this.element.find(`[name="${field}"]`);
            if (input.length) {
                stepData[field] = input.val();
            }
        });

        return frappe.call({
            method: "koraflow_core.api.signup.save_signup_step",
            args: {
                step: this.currentStep + 1,
                data: stepData
            }
        });
    }

    async completeSignup() {
        const result = await frappe.call({
            method: "koraflow_core.api.signup.complete_signup",
            args: {
                signup_id: frappe.session.get('signup_id')
            }
        });

        if (result.message.success) {
            frappe.msgprint({
                title: __("Success"),
                message: __("Signup completed! Please check your email."),
                indicator: "green"
            });
            window.location.href = "/";
        }
    }

    bindEvents() {
        // Bind form events
    }
};

// Initialize wizard
frappe.ready(() => {
    window.wizard = new koraflow.signup.Wizard($("#signup-wizard-container"));
});
```

## Step 5: Create Modern Vue 3 Component (Recommended)

**File: `apps/koraflow_core/koraflow_core/www/signup_wizard.vue`**

```vue
<script setup>
import { ref, reactive, computed } from 'vue'
import { call } from 'frappe-ui'

const currentStep = ref(0)
const signupData = reactive({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  company_name: '',
  company_size: '',
  industry: '',
  use_case: '',
  hear_about_us: '',
  newsletter_subscribe: false
})

const steps = [
  {
    title: 'Personal Information',
    description: 'Tell us about yourself',
    fields: ['first_name', 'last_name', 'email', 'phone']
  },
  {
    title: 'Company Details',
    description: 'About your company',
    fields: ['company_name', 'company_size', 'industry']
  },
  {
    title: 'Preferences',
    description: 'How can we help you?',
    fields: ['use_case', 'hear_about_us', 'newsletter_subscribe']
  }
]

const currentStepData = computed(() => steps[currentStep.value])

async function next() {
  if (currentStep.value < steps.length - 1) {
    await saveStep()
    currentStep.value++
  } else {
    await completeSignup()
  }
}

function prev() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

async function saveStep() {
  const stepData = {}
  currentStepData.value.fields.forEach(field => {
    stepData[field] = signupData[field]
  })
  
  await call('koraflow_core.api.signup.save_signup_step', {
    step: currentStep.value + 1,
    data: stepData
  })
}

async function completeSignup() {
  const result = await call('koraflow_core.api.signup.complete_signup', {
    signup_id: frappe.session.get('signup_id')
  })
  
  if (result.success) {
    window.location.href = '/'
  }
}
</script>

<template>
  <div class="signup-wizard">
    <!-- Progress indicator -->
    <div class="wizard-progress">
      <div
        v-for="(step, index) in steps"
        :key="index"
        :class="['progress-step', { active: index <= currentStep }]"
      >
        <div class="step-number">{{ index + 1 }}</div>
        <div class="step-title">{{ step.title }}</div>
      </div>
    </div>

    <!-- Step content -->
    <div class="wizard-content">
      <h2>{{ currentStepData.title }}</h2>
      <p>{{ currentStepData.description }}</p>
      
      <!-- Form fields -->
      <div class="wizard-form">
        <TextInput
          v-if="currentStepData.fields.includes('first_name')"
          v-model="signupData.first_name"
          label="First Name"
          required
        />
        <!-- Add other fields similarly -->
      </div>

      <!-- Navigation -->
      <div class="wizard-actions">
        <Button v-if="currentStep > 0" @click="prev">Back</Button>
        <Button @click="next">
          {{ currentStep === steps.length - 1 ? 'Complete' : 'Next' }}
        </Button>
      </div>
    </div>
  </div>
</template>
```

## Step 6: Using Ollama for Custom Guidance

To get AI-powered guidance for your specific requirements:

```python
from llm_service.ollama_client import OllamaClient

client = OllamaClient()

# Ask for specific guidance
prompt = """
I need to create a signup wizard with these specific requirements:
- Step 1: Basic info (name, email, password)
- Step 2: Company details (name, size, industry)
- Step 3: Preferences and use case
- Custom validation rules
- Integration with Frappe User creation

Provide Vue 3 component code and Python API methods.
"""

response = client.generate(prompt, temperature=0.7, max_tokens=3000)
print(response)
```

## Next Steps

1. **Run the Ollama guidance script** to get AI-powered recommendations
2. **Create the DocType** using the JSON structure above
3. **Implement the Python API** methods
4. **Create the Vue component** (use Vue 3 for modern apps, or vanilla JS for simpler needs)
5. **Add routing** to make it accessible at `/signup-wizard`
6. **Test each step** and validation

## Resources

- Frappe DocType Documentation: https://frappeframework.com/docs/user/en/doctype
- Vue 3 Composition API: https://vuejs.org/guide/extras/composition-api-faq.html
- Insights Setup.vue example: `bench/apps/insights/frontend/src/setup/Setup.vue`

