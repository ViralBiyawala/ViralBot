import json
from fpdf import FPDF

# Function to load the JSON file with error handling
def load_json(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
        return {}
    except json.JSONDecodeError:
        print("Error: The JSON data is malformed.")
        return {}

# Custom PDF class for formatting
class ResumePDF(FPDF):
    def header(self):
        # Skip header for this resume design
        pass

    def footer(self):
        # Skip footer for this resume design
        pass

    def add_custom_fonts(self):
        # Add the DejaVu font without the 'uni' parameter
        self.add_font('DejaVu', '', 'DejaVuSans.ttf')
        self.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf')

    def title_section(self, title):
        self.set_font('DejaVu', 'B', 12)  # Section title font size
        self.cell(0, 8, title, new_x='LMARGIN', new_y='NEXT')
        # self.ln(1)  # More space after major section
        self.line(10, self.get_y(), 200, self.get_y())  # Line under section title
        self.ln(3)  # Space after the line

    def body_text(self, text):
        self.set_font('DejaVu', '', 9)  # Reduced font size
        self.multi_cell(0, 6, text)  # Adjust line height
        self.ln(1)  # Less space between lines of information

    def bullet_point(self, text):
        text = self.clean_text(text)  # Clean the text
        self.set_font('DejaVu', '', 9)  # Consistent body text size
        self.multi_cell(0, 6, f"• {text}")  # Use bullet character
        self.ln(1)  # Less space after bullet points

    def code_block(self, text):
        text = self.clean_text(text)  # Clean the text
        self.set_font('Courier', '', 9)
        self.multi_cell(0, 6, text)
        self.ln(1)  # Less space after code blocks

    def clean_text(self, text):
        # Replace unsupported characters and filter out unsupported characters
        replacements = {
            '\u2014': '-',  # em dash
            '\u2013': '-',  # en dash
            '\u2018': "'",  # left single quote
            '\u2019': "'",  # right single quote
            '\u201C': '"',  # left double quote
            '\u201D': '"',  # right double quote
            '\u2026': '...',  # ellipsis
        }
        
        # Replace defined characters
        for original, replacement in replacements.items():
            text = text.replace(original, replacement)

        # Remove unsupported characters
        supported_characters = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,;:()[]-_/")  # Add more characters if needed
        # Exclude emojis and any unsupported characters
        return ''.join(c for c in text if c in supported_characters)

# Function to generate PDF from JSON data
def create_resume_pdf(data, output_filename):
    pdf = ResumePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Add custom fonts
    pdf.add_custom_fonts()

    # Title (Personal Information)
    pdf.set_font('DejaVu', 'B', 14)  # Name font size
    pdf.cell(0, 10, text=data['personal_info']['name'], new_x='LMARGIN', new_y='NEXT')

    pdf.set_font('DejaVu', '', 9)  # Reduced font size for personal info
    pdf.cell(0, 6, text=f"{data['personal_info']['location']} | {data['personal_info']['email']} | {data['personal_info']['phone']}", new_x='LMARGIN', new_y='NEXT')

    # Add dynamic links if available
    links = []
    if 'portfolio' in data['personal_info']:
        # add link and text to pdf instead of appending to links
        pdf.cell(0, 6, text=f"Portfolio: {data['personal_info']['portfolio']}", new_x='LMARGIN', new_y='NEXT')
        # links.append(f"Portfolio: {data['personal_info']['portfolio']}")
        # pdf.ln(1)
    if 'github' in data['personal_info']:
        # add link and text to pdf instead of appending to links
        pdf.cell(0, 6, text=f"GitHub: {data['personal_info']['github']}", new_x='LMARGIN', new_y='NEXT')
        # pdf.ln(1)
    if 'linkedin' in data['personal_info']:
        # add link and text to pdf instead of appending to links
        pdf.cell(0, 6, text=f"LinkedIn: {data['personal_info']['linkedin']}", new_x='LMARGIN', new_y='NEXT')
        # links.append(f"LinkedIn: {data['personal_info']['linkedin']}")
        # pdf.ln(1)
    # pdf.cell(0, 6, text=' | '.join(links), new_x='LMARGIN', new_y='NEXT')

    pdf.ln(8)  # Extra space after personal info

    # Index Section
    pdf.title_section("Index")
    sections = ["Education", "Experience", "Projects", "Skills", "Certifications", "Achievements"]
    for i, section in enumerate(sections, 1):
        pdf.cell(0, 6, text=f"{i}. {section}", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(8)  # Extra space after index

    # Section: Education
    pdf.title_section("Education")
    for edu in data['education']:
        pdf.set_font('DejaVu', 'B', 11)  # Bold for degree and institution
        pdf.cell(0, 6, text=f"{edu['degree']} in {edu['field']}", new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('DejaVu', '', 9)  # Regular font size for duration
        pdf.cell(0, 5, text=f"Institution: {edu['institution']}", new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 5, text=f"Duration: {edu['duration']}", new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 5, text=f"CGPA: {edu.get('cgpa', edu.get('percentage', 'N/A'))}", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(3)  # Less space between educational qualifications

    # Section: Experience
    pdf.title_section("Experience")
    for exp in data['experience']:
        pdf.set_font('DejaVu', 'B', 11)  # Bold for job title
        pdf.cell(0, 6, text=f"{exp['title']} at {exp['company']}", new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('DejaVu', '', 9)  # Regular font size for duration
        pdf.cell(0, 5, text=f"Duration: {exp['duration']}", new_x='LMARGIN', new_y='NEXT')
        for desc in exp['description']:
            pdf.bullet_point(desc['list'])
        pdf.ln(3)  # Less space after each experience

    # Section: Projects
    pdf.title_section("Projects")
    
    # List all projects with numbers
    pdf.cell(0, 6, text="This are the projects which i have done", new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('DejaVu', 'B', 11)
    for i, project in enumerate(data['projects'], 1):
        pdf.cell(0, 6, text=f"{i}. {project['title']}", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)  # Extra space after listing all projects

    # Detailed project descriptions
    for project in data['projects']:
        pdf.set_font('DejaVu', 'B', 11)  # Bold for project title
        pdf.cell(0, 6, text=project['title'], new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('DejaVu', '', 9)  # Regular font size for project description
        pdf.multi_cell(0, 6, text=project['description'])
        
        # Adding different lines for each key-value pair
        if project.get('live_link'):
            pdf.cell(0, 5, text=f"Live Link: {project['live_link']}", new_x='LMARGIN', new_y='NEXT')
        if project.get('github_link'):
            pdf.cell(0, 5, text=f"GitHub: {project['github_link']}", new_x='LMARGIN', new_y='NEXT')
        if project.get('readme'):
            pdf.body_text(project['readme'])  # Add readme if exists

        pdf.ln(4)  # More space after each project

        # Adding different lines for each key-value pair
        if project.get('live_link'):
            pdf.cell(0, 5, text=f"Live Link: {project['live_link']}", new_x='LMARGIN', new_y='NEXT')
        if project.get('github_link'):
            pdf.cell(0, 5, text=f"GitHub: {project['github_link']}", new_x='LMARGIN', new_y='NEXT')
        if project.get('readme'):
            pdf.body_text(project['readme'])  # Add readme if exists

        pdf.ln(4)  # More space after each project

    # Section: Skills
    pdf.title_section("Skills")
    for skill_type, skills in data['skills'].items():
        pdf.set_font('DejaVu', 'B', 11)  # Bold for skill type
        pdf.cell(0, 6, text=skill_type, new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('DejaVu', '', 9)  # Regular font size for skills
        pdf.multi_cell(0, 6, ' • '.join(skills))  # Combine skills into one line with bullet points
        pdf.ln(3)  # Less space between skill types

    # Section: Certifications
    pdf.title_section("Certifications")
    
    # List all certifications with numbers
    pdf.set_font('DejaVu', 'B', 11)
    for i, cert in enumerate(data['certificates'], 1):
        pdf.cell(0, 6, text=f"{i}. {cert['title']}", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)  # Extra space after listing all certifications

    # Detailed certification descriptions
    for cert in data['certificates']:
        pdf.set_font('DejaVu', 'B', 11)  # Bold for certificate title
        pdf.cell(0, 6, text=cert['title'], new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('DejaVu', '', 9)  # Regular font size for certificate details
        pdf.cell(0, 5, text=f"Institution: {cert['institution']}", new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 5, text=f"Duration: {cert['duration']}", new_x='LMARGIN', new_y='NEXT')
        if 'credential_id' in cert:
            pdf.cell(0, 5, text=f"Credential ID: {cert['credential_id']}", new_x='LMARGIN', new_y='NEXT')
        if 'certificate_link' in cert:
            pdf.cell(0, 5, text=f"Certificate Link: {cert['certificate_link']}", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(4)  # More space after each certification

    # Section: Achievements
    pdf.title_section("Achievements")
    for achievement in data['achievements']:
        pdf.set_font('DejaVu', '', 9)  # Regular font size for achievement details
        pdf.multi_cell(0, 6, text=achievement)  # Use multi_cell to handle long text
        pdf.ln(1)  # Less space between achievements

    # Save the output
    pdf.output(output_filename)

# Example usage
if __name__ == "__main__":
    resume_data = load_json('resume_data.json')  # Ensure your JSON file is named resume_data.json
    create_resume_pdf(resume_data, 'resume_output.pdf')
