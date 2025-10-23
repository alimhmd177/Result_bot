import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional

class UniversityResultsScraper:
    """Scraper for extracting student results from university portal"""
    
    def __init__(self, portal_url: str, default_password: str):
        self.portal_url = portal_url
        self.default_password = default_password
        self.session = requests.Session()
        # Add headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def login(self, university_number: str) -> bool:
        """
        Login to the university portal
        
        Args:
            university_number: Student's university number
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # First, get the login page to establish session
            response = self.session.get(self.portal_url, timeout=30)
            
            if response.status_code != 200:
                print(f"Failed to load login page: {response.status_code}")
                return False
            
            # Prepare login data
            login_data = {
                'username': university_number,
                'password': self.default_password
            }
            
            # Submit login form
            response = self.session.post(
                self.portal_url,
                data=login_data,
                timeout=30,
                allow_redirects=True
            )
            
            # Check if login was successful by looking for index.php in URL or checking response content
            if response.status_code == 200:
                # Check if we're redirected to index.php or if the response contains student data
                if 'index.php' in response.url or 'النتيجة' in response.text or 'المعدل' in response.text:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_results(self, university_number: str) -> Optional[Dict]:
        """
        Get student results from the portal
        
        Args:
            university_number: Student's university number
            
        Returns:
            Dict containing student information and results, or None if failed
        """
        try:
            # Login first
            if not self.login(university_number):
                return {
                    'success': False,
                    'error': 'فشل تسجيل الدخول. تأكد من الرقم الجامعي.'
                }
            
            # Get the main page after login
            response = self.session.get(f"{self.portal_url}/index.php", timeout=30)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': 'فشل الاتصال بالموقع.'
                }
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract student information
            student_info = {
                'success': True,
                'university_number': university_number,
                'courses': [],
                'gpa': None,
                'status': None,
                'notice': None
            }
            
            # Extract notice if exists
            notice_elements = soup.find_all(string=re.compile('النتيجة خاضعة'))
            if notice_elements:
                student_info['notice'] = notice_elements[0].strip()
            
            # Find the results table
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    
                    if len(cells) >= 2:
                        course_name = cells[0].get_text(strip=True)
                        grade = cells[1].get_text(strip=True)
                        
                        # Skip header rows
                        if course_name and grade and course_name != 'The Course' and course_name != 'المادة':
                            student_info['courses'].append({
                                'name': course_name,
                                'grade': grade
                            })
            
            # Extract GPA and status
            text_content = soup.get_text()
            
            # Look for GPA pattern
            gpa_match = re.search(r'المعدل\s*\(\s*([\d.]+)\s*\)', text_content)
            if gpa_match:
                student_info['gpa'] = gpa_match.group(1)
            
            # Look for status
            if 'نجاح' in text_content:
                student_info['status'] = 'نجاح'
            elif 'رسوب' in text_content:
                student_info['status'] = 'رسوب'
            
            return student_info
            
        except Exception as e:
            print(f"Error getting results: {e}")
            return {
                'success': False,
                'error': f'حدث خطأ أثناء استخراج النتائج: {str(e)}'
            }
    
    def format_results_message(self, results: Dict) -> str:
        """
        Format results into a readable message
        
        Args:
            results: Dictionary containing student results
            
        Returns:
            Formatted string message
        """
        if not results.get('success'):
            return f"❌ {results.get('error', 'حدث خطأ غير معروف')}"
        
        message = "📊 *نتائج الطالب*\n\n"
        message += f"🎓 *الرقم الجامعي:* `{results['university_number']}`\n\n"
        
        # Add notice if exists
        if results.get('notice'):
            message += f"⚠️ _{results['notice']}_\n\n"
        
        # Add courses
        if results.get('courses'):
            message += "📚 *المواد والدرجات:*\n"
            message += "━━━━━━━━━━━━━━━━━━━━\n"
            
            for i, course in enumerate(results['courses'], 1):
                message += f"{i}. *{course['name']}*\n"
                message += f"   📝 الدرجة: `{course['grade']}`\n\n"
        
        # Add GPA and status
        if results.get('gpa'):
            message += f"📈 *المعدل:* `{results['gpa']}`\n"
        
        if results.get('status'):
            status_emoji = "✅" if results['status'] == 'نجاح' else "❌"
            message += f"{status_emoji} *الحالة:* {results['status']}\n"
        
        return message