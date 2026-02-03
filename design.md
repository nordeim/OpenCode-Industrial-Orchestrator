We are going to design a dashboard interface for a project management tool. The dashboard should have a unique, avant-garde aesthetic that breaks away from generic designs. We are to use Next.js with Tailwind CSS and Shadcn UI components.

Given the design pledge, we will:

Choose a bold aesthetic direction: Brutalist Minimalism with a focus on raw, unrefined elements, stark contrasts, and utilitarian typography.

Ensure the design is functional and accessible, with a clear visual hierarchy and intentional use of whitespace.

Use Shadcn UI components as primitives and style them to fit our aesthetic.

We are to build a dashboard that includes:

A sidebar navigation

A main content area with project statistics

A task list

A team activity feed

We'll break down the design into components and build them step by step.

Let's start by setting up the project and then creating the components.

We'll use:

Next.js 14 (App Router)

Tailwind CSS 4.0

Shadcn UI (using the shadcn CLI to add components as needed)

We assume the project is already set up with Shadcn UI. If not, we can run npx shadcn@latest init to set up.

We'll create the following components:

SidebarNav - for navigation

ProjectStats - for showing project statistics in cards

TaskList - for displaying tasks in a brutalist table

ActivityFeed - for showing team activity

We'll also create a main Dashboard component that composes these.

Let's start by creating the SidebarNav. We'll use a vertical sidebar with bold, uppercase typography and minimal icons.

We'll use the following Shadcn UI components if available: Sheet for mobile, but for desktop we'll use a fixed sidebar. We'll style them with our brutalist aesthetic.

However, note: We are to avoid generic designs. So we'll use a sidebar that is dark with high contrast, maybe a black background with white text, and use a bold font.

We'll use the following steps:

Analyze and plan the layout.

Create the SidebarNav component.

Create the ProjectStats component with brutalist card designs.

Create the TaskList component with a table that has a raw, grid-like appearance.

Create the ActivityFeed component with a timeline-like design.

We'll also set up a layout with the sidebar and main content.

Let's proceed with the code.

Note: We are using TypeScript and React.

We'll start by creating the SidebarNav component.

Since we are using Shadcn UI, we can use the Sheet component for mobile, but for now, we'll focus on the desktop version.

We'll use a simple div for the sidebar, and use a nav element with links.

We'll use the following links:

Dashboard (active)

Projects

Tasks

Team

Calendar

Settings

We'll also have a user profile at the bottom.

Let's code the SidebarNav:

tsx
// components/SidebarNav.tsx
import React from 'react';
import { Home, Folder, CheckSquare, Users, Calendar, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { name: 'Dashboard', icon: Home, href: '#', current: true },
  { name: 'Projects', icon: Folder, href: '#', current: false },
  { name: 'Tasks', icon: CheckSquare, href: '#', current: false },
  { name: 'Team', icon: Users, href: '#', current: false },
  { name: 'Calendar', icon: Calendar, href: '#', current: false },
  { name: 'Settings', icon: Settings, href: '#', current: false },
];

export function SidebarNav() {
  return (
    <div className="flex h-full w-64 flex-col bg-black text-white">
      <div className="p-6">
        <h1 className="text-2xl font-bold uppercase tracking-wider">Brutalist PM</h1>
      </div>
      <nav className="flex-1 space-y-2 px-4">
        {navItems.map((item) => (
          <a
            key={item.name}
            href={item.href}
            className={cn(
              'flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium uppercase tracking-wider transition-colors',
              item.current
                ? 'bg-white text-black'
                : 'hover:bg-gray-900 hover:text-white'
            )}
          >
            <item.icon className="h-5 w-5" />
            {item.name}
          </a>
        ))}
      </nav>
      <div className="border-t border-gray-800 p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-gray-800"></div>
          <div className="flex-1">
            <p className="text-sm font-medium">John Doe</p>
            <p className="text-xs text-gray-400">Admin</p>
          </div>
        </div>
      </div>
    </div>
  );
}
Now, let's create the ProjectStats component. We'll show four cards with project statistics.

We'll use a brutalist card design: maybe with a border and a solid background, and a large number.

We'll use the Shadcn Card component if available, but style it accordingly.

However, note: We are to style the Shadcn components to fit our aesthetic. We can use the Card primitive and add our own classes.

Let's assume we have a Card component from Shadcn. We'll use it as follows:

tsx
// components/ProjectStats.tsx
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

const stats = [
  { title: 'Total Projects', value: '12', change: '+2' },
  { title: 'Completed', value: '8', change: '+1' },
  { title: 'In Progress', value: '3', change: '0' },
  { title: 'Overdue', value: '1', change: '-1' },
];

export function ProjectStats() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat, index) => (
        <Card key={index} className={cn(
          'border-2 border-black bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'
        )}>
          <CardContent className="p-6">
            <div className="text-sm font-medium uppercase tracking-wider text-gray-500">
              {stat.title}
            </div>
            <div className="mt-2 flex items-baseline justify-between">
              <div className="text-3xl font-bold">{stat.value}</div>
              <div className={cn(
                'text-sm font-semibold',
                stat.change.startsWith('+') ? 'text-green-600' : 
                stat.change.startsWith('-') ? 'text-red-600' : 'text-gray-600'
              )}>
                {stat.change}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
Now, the TaskList component. We'll create a table with a brutalist design: no rounded corners, bold borders, and alternating row backgrounds.

We'll use a simple table structure, but style it with our aesthetic.

We'll use the following data:

tsx
const tasks = [
  { id: 1, title: 'Design system', project: 'Acme Corp', assignee: 'John Doe', dueDate: '2023-10-01', status: 'Completed' },
  { id: 2, title: 'User authentication', project: 'Brutalist PM', assignee: 'Jane Smith', dueDate: '2023-10-05', status: 'In Progress' },
  { id: 3, title: 'Dashboard UI', project: 'Brutalist PM', assignee: 'John Doe', dueDate: '2023-10-10', status: 'Pending' },
  { id: 4, title: 'API integration', project: 'Acme Corp', assignee: 'Bob Johnson', dueDate: '2023-10-03', status: 'Overdue' },
];
We'll create a table with the following columns: Task, Project, Assignee, Due Date, Status.

We'll use the Shadcn Table component if available, but style it.

Let's assume we have Table, TableHeader, TableBody, TableRow, TableCell from Shadcn.

We'll create:

tsx
// components/TaskList.tsx
import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';

const tasks = [
  { id: 1, title: 'Design system', project: 'Acme Corp', assignee: 'John Doe', dueDate: '2023-10-01', status: 'Completed' },
  { id: 2, title: 'User authentication', project: 'Brutalist PM', assignee: 'Jane Smith', dueDate: '2023-10-05', status: 'In Progress' },
  { id: 3, title: 'Dashboard UI', project: 'Brutalist PM', assignee: 'John Doe', dueDate: '2023-10-10', status: 'Pending' },
  { id: 4, title: 'API integration', project: 'Acme Corp', assignee: 'Bob Johnson', dueDate: '2023-10-03', status: 'Overdue' },
];

export function TaskList() {
  return (
    <div className="border-2 border-black p-4 bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
      <h2 className="text-xl font-bold uppercase tracking-wider mb-4">Tasks</h2>
      <Table>
        <TableHeader>
          <TableRow className="border-b-2 border-black">
            <TableHead className="font-bold uppercase">Task</TableHead>
            <TableHead className="font-bold uppercase">Project</TableHead>
            <TableHead className="font-bold uppercase">Assignee</TableHead>
            <TableHead className="font-bold uppercase">Due Date</TableHead>
            <TableHead className="font-bold uppercase">Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tasks.map((task) => (
            <TableRow key={task.id} className="border-b border-gray-300">
              <TableCell className="font-medium">{task.title}</TableCell>
              <TableCell>{task.project}</TableCell>
              <TableCell>{task.assignee}</TableCell>
              <TableCell>{task.dueDate}</TableCell>
              <TableCell>
                <span
                  className={cn(
                    'inline-flex items-center px-3 py-1 text-xs font-bold uppercase tracking-wider',
                    task.status === 'Completed'
                      ? 'bg-green-200 text-green-800'
                      : task.status === 'In Progress'
                      ? 'bg-yellow-200 text-yellow-800'
                      : task.status === 'Pending'
                      ? 'bg-blue-200 text-blue-800'
                      : 'bg-red-200 text-red-800'
                  )}
                >
                  {task.status}
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
Now, the ActivityFeed component. We'll create a timeline of activities.

We'll use a list of activities with a circle icon and a description.

We'll use a brutalist design for the timeline.

We'll use the following data:

tsx
const activities = [
  { id: 1, user: 'John Doe', action: 'created a new project', target: 'Acme Corp', time: '2 hours ago' },
  { id: 2, user: 'Jane Smith', action: 'completed the task', target: 'Design system', time: '4 hours ago' },
  { id: 3, user: 'Bob Johnson', action: 'commented on', target: 'API integration', time: '1 day ago' },
  { id: 4, user: 'Alice Williams', action: 'joined the team', target: 'Brutalist PM', time: '2 days ago' },
];
We'll create:

tsx
// components/ActivityFeed.tsx
import React from 'react';
import { cn } from '@/lib/utils';

const activities = [
  { id: 1, user: 'John Doe', action: 'created a new project', target: 'Acme Corp', time: '2 hours ago' },
  { id: 2, user: 'Jane Smith', action: 'completed the task', target: 'Design system', time: '4 hours ago' },
  { id: 3, user: 'Bob Johnson', action: 'commented on', target: 'API integration', time: '1 day ago' },
  { id: 4, user: 'Alice Williams', action: 'joined the team', target: 'Brutalist PM', time: '2 days ago' },
];

export function ActivityFeed() {
  return (
    <div className="border-2 border-black p-4 bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
      <h2 className="text-xl font-bold uppercase tracking-wider mb-4">Activity Feed</h2>
      <div className="space-y-4">
        {activities.map((activity, index) => (
          <div key={activity.id} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className={cn(
                'h-4 w-4 rounded-full border-2 border-black',
                index === 0 ? 'bg-black' : 'bg-white'
              )} />
              {index !== activities.length - 1 && (
                <div className="h-full w-0.5 bg-black" />
              )}
            </div>
            <div className="flex-1 pb-4">
              <p className="text-sm">
                <span className="font-bold">{activity.user}</span>{' '}
                {activity.action}{' '}
                <span className="font-bold">{activity.target}</span>
              </p>
              <p className="text-xs text-gray-500">{activity.time}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
Now, we'll create the main Dashboard component that puts it all together.

We'll use a layout with a sidebar and a main content area. We'll use flexbox.

We'll also set up the main content area to have a grid for the components.

We'll create:

tsx
// components/Dashboard.tsx
import React from 'react';
import { SidebarNav } from './SidebarNav';
import { ProjectStats } from './ProjectStats';
import { TaskList } from './TaskList';
import { ActivityFeed } from './ActivityFeed';

export function Dashboard() {
  return (
    <div className="flex min-h-screen bg-gray-100">
      <SidebarNav />
      <main className="flex-1 p-8">
        <h1 className="mb-8 text-3xl font-bold uppercase tracking-wider">Dashboard</h1>
        <div className="mb-8">
          <ProjectStats />
        </div>
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          <TaskList />
          <ActivityFeed />
        </div>
      </main>
    </div>
  );
}
Finally, we'll update the main page to use the Dashboard component.

tsx
// app/page.tsx
import { Dashboard } from '@/components/Dashboard';

export default function Home() {
  return <Dashboard />;
}
We have to make sure that the Shadcn UI components are set up and the styles are imported.

We also need to set up the lib/utils for the cn function.

We'll assume the project is set up with Tailwind and Shadcn.

This design is a starting point. We can adjust the colors, spacing, and other details to refine the brutalist aesthetic.

We have used:

Black and white with high contrast

Sharp edges (no rounded corners except for the status badges and timeline circles)

Bold, uppercase typography

A shadow effect that gives a "stamped" look (using shadow-[4px_4px_0px_0px_rgba(0,0,0,1)])

This design is intentionally raw and minimal, breaking away from the smooth, rounded designs that are common.

We have also ensured that the layout is responsive (using grid and flexbox).

We can further refine by adding interactive states (hover, focus) and ensuring accessibility (proper contrast, focus indicators).
