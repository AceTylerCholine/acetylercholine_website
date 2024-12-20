#!/usr/bin/perl

#-------------------------------------------------------------------
# ONLINE Timeline Followback (TLFB)
#
# You may copy this software, and use it however you see fit.
# No guarantee or warranty of any kind is provided.
# Note that you will need to make a few modifications to the code to
#   customize for your setup.  
#  * setup your database (schema available at URL below)
#  * add your database name, username, and password to $dbh
#  * make sure permissions are set appropriately for this script and the db
# You should be good to go!  
#
# Joel Grow 
# http://depts.washington.edu/abrc/tlfb/
#-------------------------------------------------------------------

use strict;
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use DBI;
use Date::Manip;


#-------------------------------------------------------------------
# Fill this in with your database name, username, and password
#-------------------------------------------------------------------

my $dbh = DBI->connect(DSN, USER, PW)
          or die "Can't connect to db:" . DBI::errstr;


my $homepage = 'http://depts.washington.edu/abrc/tlfb/';

my $q = CGI->new;

#NOTE:
# this can't go above 364.
# 1 gets added to this number, for the total numbers of days displayed.
my $DAYS_TO_DISPLAY = 99;

# constants
my $DATE_FORM_MM   = 'a_';
my $DATE_FORM_DD   = 'b_';
my $DRINKS_FORM    = 'd_';
my $HOURS_FORM     = 'e_';
my $JOINTS_FORM    = 'f_';

# actions
my $DEFAULT_ACTION       = 'g_';
my $DISPLAY_INSTRUCTIONS = 'h_';
my $DISPLAY_MARKER_PAGE  = 'i_';
my $DISPLAY_CALENDAR     = 'j_';
my $PROCESS_ADD_MARKER   = 'l_';
my $PROCESS_CALENDAR     = 'm_';


my %months = (1 => 'January',
              2 => 'February',
              3 => 'March',
              4 => 'April',
              5 => 'May',
              6 => 'June',
              7 => 'July',
              8 => 'August', 
              9 => 'September',
              10 => 'October',
              11 => 'November',
              12 => 'December',
        );

my $SELF = $q->url('relative => 1');

my %dispatch = (
        $DEFAULT_ACTION       => \&page_one,
        $DISPLAY_INSTRUCTIONS => \&display_instructions,
        $DISPLAY_MARKER_PAGE  => \&display_marker_page,
        $PROCESS_ADD_MARKER   => \&process_add_marker,
        $DISPLAY_CALENDAR     => \&display_calendar,
        $PROCESS_CALENDAR     => \&process_calendar,
        );

my $action = $q->param('action');
my $subref = $dispatch{$action} || $dispatch{$DEFAULT_ACTION};

print_header();

$subref->();

print_footer();

exit;


sub process_add_marker {
    my $participant_id = $q->param('participant_id');

    my $insert_sql = <<End_of_SQL;
INSERT INTO marker_days 
(participant_id, date, description)
VALUES (?, ?, ?)
End_of_SQL

    my $sth = $dbh->prepare($insert_sql)
        or die "Can't prepare: " . $dbh->errstr;

    my $markers_added = 0;
    foreach my $i (1..10) { 
        my $description = $q->param("description_$i");
        my $mm   = $q->param("${DATE_FORM_MM}_$i");
        my $dd   = $q->param("${DATE_FORM_DD}_$i");

        next unless ($mm and $dd and $description);

        my $date = make_date({ mm => $mm, dd => $dd });

        $sth->execute($participant_id, $date, $description)
            or die "Can't execute: " . $sth->errstr;

        $markers_added++;
    }

    $dispatch{$DISPLAY_CALENDAR}->("$markers_added markers added");
}


sub display_calendar {
    my $msg = shift;

#
# these 2 set the time boundaries
# start_date: ($DAYS_TO_DISPLAY days ago) - stop_date
#
# current_day: holds the current marker day
# 
# previous month/year is the referer month/year
#

    my $participant_id = $q->param('participant_id');

    my $select_sql = <<End_of_SQL;
SELECT *
FROM   marker_days
WHERE  participant_id=?
End_of_SQL

    my $sth = $dbh->prepare($select_sql)
        or die "Couldn't prepare: " . $dbh->errstr;

    $sth->execute($participant_id) or die "Couldn't execute: " . $sth->errstr;

    # build %marker_days hash
    my %marker_days;
    while (my $r_row = $sth->fetchrow_hashref) {
        my $date        = $r_row->{date};  # MM/DD, no 0's
        my $description = $r_row->{description};

        $marker_days{$date} = $description;
    }

    my $prevmonthsubmit        = $q->param('prevmonthsubmit');
    my $nextmonthsubmit        = $q->param('nextmonthsubmit');
    my $finalsubmit            = $q->param('finalsubmit');
    my $previous_month         = $q->param('previous_month');
    my $previous_year          = $q->param('previous_year');

    my $stop_date   = UnixDate('today', "%Y%m%d");
    my $start_date  = UnixDate(
                        DateCalc($stop_date, "-$DAYS_TO_DISPLAY days"),
                        "%Y%m%d"
                      );
    my ($stop_yyyy, $stop_mm) = ($stop_date =~ /^(\d{4})(\d\d)/);

    my $current_day;
    if ($finalsubmit) {
        $dispatch{$PROCESS_CALENDAR}->($participant_id, $start_date, $stop_date);
        return;
    } elsif ($prevmonthsubmit) {
        $current_day = 
            UnixDate(
                    DateCalc("$previous_year/$previous_month/01", "-1 month"),
                    "%Y%m%d"
                    );
    } elsif ($nextmonthsubmit) {
        $current_day = 
            UnixDate(
                    DateCalc("$previous_year/$previous_month/01", "+1 month"),
                    "%Y%m%d"
                    );
    } else {
        $current_day = "$stop_yyyy${stop_mm}01";
    }

    my ($current_yyyy, $current_mm, $current_dd) = 
        $current_day =~ /^(\d{4})(\d{2})(\d{2})/;

    # returns 1 (Monday) to 7 (Sunday)
    my $first_day_of_month = UnixDate("$current_yyyy/$current_mm/01", "%w");
    my $days_in_month      = Date_DaysInMonth($current_mm, $current_yyyy);
    my $month_string       = UnixDate("$current_yyyy/$current_mm/$current_dd", "%B");


    print qq{<font color="red">$msg</font><br /><br />} if ($msg);

    print_instructions();

    print qq{
<div align="center">
  <center>
  <form action="$SELF" method="POST">
<table border="1" width="675" cellspacing="0" bgcolor="#FFFFFF" bordercolor="#808080" style="border-collapse: collapse">
     <tr>
      <td width="675" colspan="7" height="44">
        <p align="center">&nbsp;<br /><b><font face="Helvetica" size="5">$month_string $current_yyyy</font></b><br>
        <font size="2">&nbsp;</font>
      </p>
     </td>
    </tr>
    <tr>
      <td width="94" height="17">
        <p align="center"><strong><font size="2" face="Helvetica">Sunday</font></strong></td>

      <td width="94" height="17">
        <p align="center"><font size="2" face="Helvetica"><strong>Monday</strong></font></td>
      <td width="94" height="17">
        <p align="center"><font size="2" face="Helvetica"><strong>Tuesday</strong></font></td>
      <td width="94" height="17">
        <p align="center"><font size="2" face="Helvetica"><strong>Wednesday</strong></font></td>
      <td width="94" height="17">

        <p align="center"><font size="2" face="Helvetica"><strong>Thursday</strong></font></td>
      <td width="95" height="17">
        <p align="center"><font size="2" face="Helvetica"><strong>Friday</strong></font></td>
      <td width="95" height="17">
        <p align="center"><font size="2" face="Helvetica"><strong>Saturday</strong></font></td>
    </tr>
    };

    # find first day of the month
    print '<tr>';

    my $row_cell_count = 0;
    for my $dow (7, 1..6) {
        if ($first_day_of_month == $dow) {
            last;

        } else {
            $row_cell_count++;
            print qq{
  <td class="day other_month" width="94" height="107" align="left" valign="top">
   <font size="1">&nbsp;</font><font size="2"><b>&nbsp;</b></font></td>
            };
        }
    }

    for my $dom (1..$days_in_month) {
        if ($row_cell_count == 7) {
            print '</tr><tr>';
            $row_cell_count = 1;
        } else {
            $row_cell_count++;
        }

        my $comparison_date = sprintf("%d%02d%02d",$current_yyyy, $current_mm, $dom);
        if ($comparison_date >= $start_date and
            $comparison_date <= $stop_date) {

            my $comparison_mmdd = sprintf("%d/%d", $current_mm, $dom);
            my $marker_description = $marker_days{$comparison_mmdd};

            my ($marker_html, $class_text);
            if ($marker_description) {
                $marker_html = 
                   qq{<font color="red">$marker_description</font><br /><br />};
                $class_text = qq{class="day marker"};
            }

            print qq{
                    <td $class_text width="94" height="107" align="left" valign="top">
                     <font size="1">&nbsp;</font>
                     <b><font size="2">$dom</font></b>
                     <br /><br />$marker_html
            };

            # table cell
            print '<font face="Helvetica" size="2">Drinks: ', 
                  $q->textfield(-name => "${DRINKS_FORM}_$comparison_date",
                          -size => 2),
                  '<br />Hours: ', 
                  $q->textfield(-name => "${HOURS_FORM}_$comparison_date",
                          -size => 2),

                  '<br />Joints: ',
                  $q->textfield(-name => "${JOINTS_FORM}_$comparison_date",
                          -size => 2),

                  '</font>';
          

            print ' </td>';

        } else {
            print qq{
     <td class="day noform" width="94" height="107" align="left" valign="top">
       <font size="1">&nbsp;</font>
       <b><font size="2">$dom</font></b>
     </td>
            };
        }
    }

    for my $eom_filler ($row_cell_count..6) {
        print qq{
  <td class="day other_month" width="94" height="107" align="left" valign="top">
   <font size="1">&nbsp;</font><font size="2"><b>&nbsp;</b></font>
   </td>
        };
    }

    print qq{
 </tr>
 <tr bgcolor="#9EA4A6" align="center"><td colspan="7">
 <input type="hidden" name="previous_month" value="$current_mm">
 <input type="hidden" name="previous_year" value="$current_yyyy">
 <input type="hidden" name="participant_id" value="$participant_id">
 <input type="hidden" name="action" value="$DISPLAY_CALENDAR">
    };

    my $next_month = UnixDate(
                        DateCalc($current_day, "+1 month"),
                        "%Y%m01"
            );

    if ($start_date < $current_day) {
        print 
        '<input type="submit" name="prevmonthsubmit" value="Previous Month">';
    } else {
        print '<input type="submit" name="finalsubmit" value="Calendar Complete">';
    }

    if ($stop_date > $next_month) {
        print '<input type="submit" name="nextmonthsubmit" value="Next Month">';
    } 

    foreach my $drink_form_var (grep { /${DRINKS_FORM}_/ } $q->param) {
        my $drink_val = $q->param($drink_form_var);
        print qq{<input type="hidden" name="$drink_form_var" value="$drink_val">\n};
    }
    foreach my $joints_var (grep { /${JOINTS_FORM}_/ } $q->param) {
        my $joints_val = $q->param($joints_var);
        print qq{<input type="hidden" name="$joints_var" value="$joints_val">\n};
    }
    foreach my $hours_var (grep { /${HOURS_FORM}_/ } $q->param) {
        my $hours_val = $q->param($hours_var);
        print qq{<input type="hidden" name="$hours_var" value="$hours_val">\n};
    }

    print '</form></td></tr></table>';

}


sub display_instructions {
    my $participant_id = $q->param('participant_id');
    my $sessionid     = $q->param('sessionid');

    if (!$participant_id) {
        $dispatch{$DEFAULT_ACTION}->();
        return;
    }

    print qq{
<div class="titlebox">
INSTRUCTIONS for Filling Out the Timeline Alcohol and Marijuana Use Calendar
</div>
<br />

To help us evaluate your drinking and marijuana use, we need to get an idea of
what your alcohol use was like in the <strong>past 90 days</strong>.  To do
this, we would like you to fill out the attached calendar. 

<br />
<ul>

<li>Filling out the calendar is not hard!</li>
<li>Try to be as accurate as possible.</li>
<li>We recognize you won't have perfect recall. That's OKAY.</li>
</ul>
<br />

<strong>WHAT TO FILL IN (Alcohol and Marijuana Use)</strong>
<br />
<br />
<strong>DRINKING:</strong>
<br />
<ul>
<li>DRINKS: The idea is to put a number in the box labeled DRINKS for each day on the calendar.</li>
<br />
<li>HOURS: For each day that you consumed any alcohol, please indicate how many
hours you spent drinking that day; that is, from your first sip of alcohol to
when you finished your last drink.</li>
<br />
<li >
On days when you did not drink, you should type a 0 in the box that says DRINKS. You can leave the HOURS box blank.</li>
<br />
<li>We want you to record your drinking on the calendar using Standard Drinks.
For example, if you had 6 beers, type the number 6 for that day. If you drank
two or more different kinds of alcoholic beverage in a day such as 2 beers and
3 glasses of wine, you would type the number 5 for that day.</li>
</ul>
One standard drink is defined as:
<br />
<ul>
<li> <strong>12 oz. of beer</strong> (8 oz. Canadian beer, malt liquor, or ice beers or 10 oz. of microbrew)
<ul>
<li>Beers may come in 12 oz., 16oz. or 22 oz. cans. Consider the container you typically drink from.</li>
<li>40 oz. of malt liquor is 5 drinks. 40 oz. of regular beer is about 3 drinks.</li>
</ul>
</li>
<li>10 oz. of wine cooler (e.g., Mike's Hard Lemonade, Smirnoff Ice)</li>
<li><strong>4 oz. of wine</strong>
<ul><li>About one half of a glass is 4 oz. One bottle of wine is about 5 drinks.
</li></ul>
<li>1 oz. (one shot) of 100 proof liquor</li>
<li>1 1/4 oz. (one shot) of 80 proof liquor</li>
<li><strong>1 cocktail with 1 oz. of 100 proof or 1 1/4 oz. of 80 proof liquor</strong>

<ul><li>A mixed drink with three shots is considered 3 drinks
</li></ul>
</li>
</ul>
<br />
MARIJUANA:
<br />
<ul>
<li>Again the idea is to put a number in for <strong>each day</strong> on the calendar.</li>
<br />
<li>JOINTS: On days when you used marijuana, please indicate how many times that
day you used marijuana. Consider one JOINT to be one occasion where
you smoked one joint, bowl, pipe, bong, vaporizer, etc. within one time period.
For example, if you and two friends split one bowl, that would be one occasion.
If you repacked it and smoked again, that would be two occasions. If you smoked
once at 2pm and again at 7pm, this would be two JOINTS. 
</li>
<br />
<li>
Remember JOINTS = "number of times you smoked during that particular day."
</li>
<br />
<li>
On days when you did not use marijuana, please type 0 for marijuana use. 
</li>
</ul>
<strong>
It's important that something is typed in the DRINKS and JOINTS boxes for every day, even if it is a "0".
</strong>
<br />
<br />


<strong>YOUR BEST ESTIMATE 
</strong>
<br />
<ul>
<li>We realize it isn't easy to recall things with 100% accuracy. </li>
<br />
<li>If you are not sure whether you drank 7 or 11 drinks or whether you drank
on a Thursday or a Friday, <strong>give it your best guess!</strong> 
What is important is that 7
or 11 drinks is very different from 1 or 2 drinks or 25 drinks. The goal is to
get a sense of how frequently you drank, how much you drank, and your patterns
of drinking. 
</li>
<br />

<li>The same goes for marijuana use. If you do remember if you smoked on a
Friday or a Saturday, just pick one. Just do the best you can to remember your
behavior over the past three months. </li>

</ul>
<br />
<strong>HELPFUL HINTS</strong>
<br />
<ul>
<li>If you have an appointment book you can use it to help you recall your
drinking and marijuana use.</li>
<br />

<li>On the next page, you will indicate certain holidays, personal events, special
occasions, etc. that will help you recall your use over the past 90 days. These
events will be preloaded into the assessment to help you remember your
behaviors. </li>
<br />

<li>If you have regular drinking patterns you can use these to help you recall
your drinking. For example, you may have a daily or weekend/weekday pattern, or
drink more in the summer or on trips, or you may drink on Wednesdays after
playing sports. You may typically smoke when watching a particular TV show on
Thursday nights or when hanging out with a certain group of friends you only
see every other week. 
</li>
<br />
<li>
We realize it isn't easy to recall things with 100% accuracy. If you are not
sure whether you drank 7 or 11 drinks or whether you drank on a Thursday or a
Friday, give it your best guess! What is important is that 7 or 11 drinks are
very different from 1 or 2 drinks or 25 drinks. The goal is to get a sense of
how frequently you drank, how much you drank, and your patterns of drinking.
The same goes for marijuana use. If you do not remember if you smoked on a
Friday or a Saturday, just pick one. Just do the best you can to remember your
behavior over the past three months.
</li>
</ul>
<br />
<strong>COMPLETING THE CALENDAR </strong>
<br />
First view the sample calendar so you have a sense of what the assessment should look like:
<br />
<br />
<img width="636" height="487" src="calendar_image.png"  alt="calendar example">
<br />
<br />
On the next page you'll fill in marker days.
<br />
<br />
<form action="$SELF" method="POST">
<input type="hidden" name="action" value="$DISPLAY_MARKER_PAGE">
<input type="hidden" name="participant_id" value="$participant_id">
<input type="submit" value="Next">
</form>
</div>
    };
}

sub display_marker_page {
    my $participant_id = $q->param('participant_id');

    print qq{
<div class="titlebox">MARKER Days</div>
Before you are presented with the calendar, please take a moment to recall
certain holidays, birthdays, newsworthy events and other personal
events that are meaningful to you. These (whether involving alcohol and
marijuana use or not) can assist in recall of your behavior over the past three
months. Please consider national holidays (such as Labor Day [September 6th],
Columbus Day [October 11th], Halloween [October 31st]), important school dates
like the day you moved back to campus and the day classes started, major
sporting events like Huskies Football games, major news events, your own or
others' birthdays, vacation beginning and end dates, or other dates of
important personal events (such as changing jobs, buying a house, starting a
new romantic relationship, a breakup).
<br /><br />
Please enter up to 10 personal marker days. An example is provided:
<br /><br />
<table  border="1" cellspacing="0" cellpadding="0">
<tr><td>
<form action="$SELF" method="POST">
<table border="0" cellspacing="1" cellpadding="4">
<tr bgcolor="#cccccc"><td>&nbsp;</td><td><strong>Date</strong></td><td><strong>Event</strong></td></tr>
<tr bgcolor="#eeeeee"><td><i>Example</i></td><td> 7/31</td><td> my birthday</td></tr>
    };

    my $rowcolor = 'dddddd';

    for my $rowcount (1..10) {
        print qq{
            <tr bgcolor="#$rowcolor"><td>$rowcount.</td>
            <td>
            <select name="${DATE_FORM_MM}_$rowcount"> 
        };
        print qq{<option value="0">Select month</option>\n};
        foreach my $month (1..12) {
            print qq{<option value="$month">$months{$month}</option>\n};
        }

        print qq{</select> <select name="${DATE_FORM_DD}_$rowcount"> 
             <option value="0">Day</option>
        };

        foreach my $day (1..31) {
            print qq{<option value="$day">$day</option>\n};
        }

        print qq{</select></td>
            <td><input size="30" type="text" name="description_$rowcount"></td>
            </tr>
        };

        $rowcolor = $rowcolor eq 'dddddd' ? 'eeeeee' : 'dddddd';
    }

    print qq{
</table>
</td></tr></table>
<br />
<input type="hidden" name="action" value="$PROCESS_ADD_MARKER">
<input type="hidden" name="participant_id" value="$participant_id">
<input type="submit" value="Done with markers">
</form>
    };
}

sub print_footer {
    print '</div>';
    print $q->end_html;
}

sub print_header {
    print $q->header;
    print qq{
<html>

<head>
<link rel="stylesheet" href="reset_base.css" type="text/css">
<link rel="stylesheet" href="global.css" type="text/css">
<title>TLFB Study</title>
</head>

<body>
<div id="main">
<div id="uwbar">
<div id="logo">
 <img src="UW.Signature_left.jpg" alt="University of Washington" width="400">
</div>
 <div id="pagetitle">
  Online Timeline Followback Demonstration
 </div>
<br />
<a href="$homepage">Back to online TLFB homepage</a>
</div>
<br />
<div class="outlinebox">
    };
}

sub print_instructions {
    print qq{
Remember, DRINKS = standard drinks. HOURS = hours spent drinking alcohol. 
JOINTS = number of occasions you used marijuana.
<ul>
<li>  <strong>12 oz. of beer</strong> (8 oz. Canadian beer, malt liquor, or ice beers or 10 oz. of microbrew)
<ul><li>       Beers may come in 12 oz., 16oz. or 22 oz. cans. Consider the container you typically drink from.</li>
<li>       40 oz. of malt liquor is 5 drinks. 40 oz. of regular beer is about 3 drinks.</li>
</ul>
</li>
<li>    10 oz. of wine cooler (e.g., Mike's Hard Lemonade, Smirnoff Ice)</li>
<li>    <strong>4 oz. of wine</strong>
<ul><li>       About one half of a glass is 4 oz. One bottle of wine is about 5 drinks.</li></ul></li>
<li>   1 oz. (one shot) of 100 proof liquor</li>
<li>    1 1/4 oz. (one shot) of 80 proof liquor</li>
<li>   <strong> 1 cocktail with 1 oz. of 100 proof or 1 1/4 oz. of 80 proof liquor</strong></li>
<ul><li>   A mixed drink with three shots is considered 3 drinks</li></ul>
</li>
</ul>
You can fill out each month of the calendar one at a time, or jump
around if it is easier for you to remember. You can click "previous month" or
"next month" to shuffle between months. 
<br /><br />Please make sure to fill
out all 90 days of the calendar. On the final page of the calendar, you will be
able to click "calendar complete" to advance to the next portion of the
assessment.
<br />
<br />

</font>
    };
}

    
sub page_one {
    my $participant_id = $q->param('participant_id');

    if ($participant_id) {
        $dispatch{$DISPLAY_INSTRUCTIONS}->();
    } else {
        print qq{
        <div class="titlebox">WELCOME to the Timeline Alcohol/Drug Use Calendar
        </div>
        Enter your participant id to begin.  
<br />
    (<i>note: for this demonstration TLFB, you can enter any string here</i>)
        <br />
        <br />
        <form action="$SELF" method="POST">
        Participant id? <input type="text" name="participant_id">
        <br />
        <br />
        <input type="hidden" name="action" value="$DISPLAY_INSTRUCTIONS">
        <input type="submit" value="Begin">
        </form>
        };
    }
}

sub make_date {
    my $rh_date = shift;
    my $date = join('/', $rh_date->{mm}, $rh_date->{dd});
    return $date;
}

sub process_calendar {
    my ($participant_id, $start_date, $stop_date) = @_;

    print "SAVING Calendar Data for participant '$participant_id'...  ";

    my $insert_sql = <<End_of_SQL;
INSERT INTO tlfb
(participant_id, date, drinks, hours, joints)
VALUES
(?, ?, ?, ?, ?)
End_of_SQL

    my $sth = $dbh->prepare($insert_sql) 
                  or die "Couldn't prepare insert: " . $dbh->errstr;

    my $current_date = $start_date;
    while ($current_date <= $stop_date) {
        my $drink_val  = $q->param("${DRINKS_FORM}_$current_date") || 0;
        my $hours_val  = $q->param("${HOURS_FORM}_$current_date")  || 0;
        my $joints_val = $q->param("${JOINTS_FORM}_$current_date") || 0;

        $sth->execute($participant_id, $current_date, $drink_val, $hours_val, $joints_val)
            or die "Couldn't execute for day $current_date: " . $sth->errstr;

        $current_date = UnixDate(DateCalc($current_date, "+1 days"), "%Y%m%d");
    }

    print qq{
      DONE!
        <br />
        <br />
<a href="$homepage">Back to the online TLFB homepage</a>
    };

}