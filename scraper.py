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
        
    def login_and_get_results(self, university_number: str) -> Optional[Dict]:
        """
        Login to the university portal and get student results
        
        Args:
            university_number: Student's university number
            
        Returns:
            Dict containing student information and results, or None if failed
        """
        try:
            # Step 1: Get the login page to establish session
            response = self.session.get(self.portal_url, timeout=30)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': 'فشل الاتصال بموقع الجامعة.'
                }
            
            # Step 2: Submit login form
            login_data = {
                'username': university_number,
                'password': self.default_password
            }
            
            # The form action is "index.php", so we post to that URL
            response = self.session.post(
                f"{self.portal_url}/index.php",
                data=login_data,
                timeout=30,
                allow_redirects=True
            )
            
            # Step 3: Check if login was successful
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': 'فشل تسجيل الدخول. تأكد من الرقم الجامعي.'
                }
            
            # CRITICAL: Set the correct encoding for Arabic content
            response.encoding = 'windows-1256'
            
            # Check if we're logged in by looking for student data
            if university_number not in response.text:
                return {
                    'success': False,
                    'error': 'فشل تسجيل الدخول. تأكد من الرقم الجامعي.'
                }
            
            # Step 4: Parse the results from the current page
            # Use lxml parser which is more forgiving with malformed HTML
            soup = BeautifulSoup(response.content, 'lxml', from_encoding='windows-1256')
            
            return self._parse_results(soup, university_number)
            
        except Exception as e:
            print(f"Error in login_and_get_results: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'حدث خطأ أثناء استخراج النتائج: {str(e)}'
            }
    
    def _parse_results(self, soup: BeautifulSoup, university_number: str) -> Dict:
        """
        Parse the results from the HTML page
        
        Args:
            soup: BeautifulSoup object of the page
            university_number: Student's university number
            
        Returns:
            Dict containing parsed results
        """
        try:
            # Extract student information
            student_info = {
                'success': True,
                'university_number': university_number,
                'courses': [],
                'gpa': None,
                'status': None,
                'notice': None
            }
            
            # Get all text content
            text_content = soup.get_text()
            
            # Extract notice if exists
            notice_match = re.search(r'النتيجة خاضعة لإجازة اللجنة العليا للامتحانات', text_content)
            if notice_match:
                student_info['notice'] = notice_match.group(0).strip()
            
            # Find all tables
            tables = soup.find_all('table')
            
            for table in tables:
                # Look for the results table by finding rows with course data
                rows = table.find_all('tr')
                
                # Check if this table has the results header
                has_results_header = False
                for row in rows:
                    if 'The Course' in row.get_text() and 'Grade' in row.get_text():
                        has_results_header = True
                        break
                
                if not has_results_header:
                    continue
                
                # Now extract courses from this table
                for row in rows:
                    # Skip header rows
                    if 'The Course' in row.get_text():
                        continue
                    
                    # Look for rows with th (course name) and td (grade)
                    th_elements = row.find_all('th')
                    td_elements = row.find_all('td')
                    
                    if th_elements and td_elements:
                        course_name = th_elements[0].get_text(strip=True)
                        grade = td_elements[0].get_text(strip=True)
                        
                        # Add if both are not empty
                        if course_name and grade:
                            student_info['courses'].append({
                                'name': course_name,
                                'grade': grade
                            })
            
            # Extract GPA and status
            gpa_match = re.search(r'المعدل\s*\(\s*([\d.]+)\s*\)', text_content)
            if gpa_match:
                student_info['gpa'] = gpa_match.group(1)
            
            # Look for status
            if 'نجاح' in text_content:
                student_info['status'] = 'نجاح'
            elif 'رسوب' in text_content:
                student_info['status'] = 'رسوب'
            
            # If no courses found but we have GPA, still return success
            # (some students might not have detailed course breakdown)
            if not student_info['courses'] and not student_info['gpa']:
                return {
                    'success': False,
                    'error': 'لم يتم العثور على نتائج. قد لا تكون النتيجة متاحة بعد.'
                }
            
            return student_info
            
        except Exception as e:
            print(f"Error parsing results: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'حدث خطأ أثناء معالجة النتائج: {str(e)}'
            }
    
    def get_results(self, university_number: str) -> Optional[Dict]:
        """
        Main method to get student results
        
        Args:
            university_number: Student's university number
            
        Returns:
            Dict containing student information and results
        """
        return self.login_and_get_results(university_number)
    
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