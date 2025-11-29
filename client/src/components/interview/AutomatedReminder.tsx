import { AlertCircle, Clock, BookOpen, Lightbulb } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface AutomatedReminderProps {
  role: string;
  interviewType: string;
  candidateName: string;
}

export function AutomatedReminder({ role, interviewType, candidateName }: AutomatedReminderProps) {
  // Determine the reminder content based on role and interview type
  const getReminderContent = () => {
    // Specific reminders based on role
    const roleSpecificTips: Record<string, string[]> = {
      'Machine Learning Engineer': [
        'Review your understanding of key concepts in the area of your expertise',
        'Be prepared to explain decisions made in your projects',
        'Have real life examples of your work ready',
        "Don't be afraid to ask questions",
      ],
      'Data Scientist': [
        'Be ready to discuss statistical significance and hypothesis testing',
        'Review common data cleaning and preprocessing techniques',
        'Prepare examples of data visualization approaches for different scenarios',
      ],
      'Frontend Engineer': [
        'Review React component lifecycle methods and hooks',
        'Be prepared to discuss state management approaches',
        'Have examples of performance optimization techniques ready',
      ],
      'Backend Engineer': [
        'Review API design principles and RESTful architecture',
        'Be prepared to discuss database optimization strategies',
        'Have examples of scalable architecture patterns ready',
      ],
      'DevOps Engineer': [
        'Be ready to discuss CI/CD pipeline implementation strategies',
        'Review containerization and orchestration concepts',
        'Prepare examples of infrastructure monitoring approaches',
      ],
      'Product Manager': [
        'Be prepared to discuss product prioritization frameworks',
        'Review user research methodologies and their applications',
        'Have examples of cross-functional collaboration approaches ready',
      ],
    };

    // Use role-specific tips or fall back to general tips
    const tips = roleSpecificTips[role] || [
      'Think out loud to share your thought process with the interviewers',
      'Ask clarifying questions when needed',
      'Focus on structured, systematic approaches to problem-solving',
    ];

    return {
      title: `${candidateName}'s ${interviewType} Reminder`,
      tips,
    };
  };

  const reminderContent = getReminderContent();

  return (
    <Alert className="bg-amber-50 border border-amber-200 my-4">
      <AlertCircle className="h-4 w-4 text-amber-600" />
      <AlertTitle className="text-amber-800 font-medium flex items-center">
        <Clock className="h-4 w-4 mr-2" />
        {reminderContent.title}
      </AlertTitle>
      <AlertDescription className="text-amber-700 mt-2">
        <p className="mb-2 flex items-center">
          <BookOpen className="h-4 w-4 mr-2 flex-shrink-0" />
          <span>
            A few minutes of preparation can make a significant difference in your interview
            performance.
          </span>
        </p>
        <div className="ml-6 mt-2">
          <p className="font-medium mb-1 flex items-center">
            <Lightbulb className="h-4 w-4 mr-1" /> Key preparation tips:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            {reminderContent.tips.map((tip, index) => (
              <li key={index}>{tip}</li>
            ))}
          </ul>
        </div>
      </AlertDescription>
    </Alert>
  );
}
