<?php defined('BASEPATH') OR exit('No direct script access allowed');

/* ==============================================================
 *
 * Bash
 *
 * ==============================================================
 *
 * @copyright  2017 David Bowes, University of Hertfordshire
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

require_once('application/libraries/LanguageTask.php');

class Sh_Task extends Task {
    public function __construct($source, $filename, $input, $params) {
        /*
        $params['memorylimit'] = 0;    // Disregard memory limit - let JVM manage memory
        $this->default_params['numprocs'] = 256;     // Java 8 wants lots of processes
        $this->default_params['interpreterargs'] = array(
             "-Xrs",   //  reduces usage signals by java, because that generates debug
                       //  output when program is terminated on timelimit exceeded.
             "-Xss8m",
             "-Xmx200m"
        );
         
         */

        $this->default_params['numprocs'] = 256;
        if (isset($params['numprocs']) && $params['numprocs'] < 256) {
            $params['numprocs'] = 256;  // Minimum for Java 8 JVM
        }

        $this->default_params['memorylimit'] = 20000000;
        if (isset($params['memorylimit']) && $params['memorylimit'] < 20000000) {
            $params['memorylimit'] = 20000000;  // Minimum for Java 8 JVM
        }

        $this->default_params['cputime'] = 10;
        if (isset($params['cputime']) && $params['cputime'] < 10) {
            $params['cputime'] = 10;  // Minimum for Java 8 JVM
        }

        Task::__construct($source, $filename, $input, $params);

        // Superclass constructor calls subclasses to get filename if it's
        // not provided, so $this->sourceFileName should now be set correctly.
        $extStart = strpos($this->sourceFileName, '.');  // Start of extension
        $this->mainClassName = substr($this->sourceFileName, 0, $extStart);
    }

    public static function getVersionCommand() {
        return array('bash -version', '/GNU bash, version "?([0-9._]*)/');
    }

    public function compile() {
        $prog = file_get_contents($this->sourceFileName);
        $compileArgs = $this->getParam('compileargs');
        $cmd = 'chmod +x'  . " {$this->sourceFileName} && dos2unix {$this->sourceFileName}  2>compile.out";
        exec($cmd, $output, $returnVar);
        if ($returnVar == 0) {
            $this->executableFileName = $this->sourceFileName;
        }
        else {
            $this->cmpinfo .= file_get_contents('compile.out');
        }
    }

    // A default name for Java programs. [Called only if API-call does
    // not provide a filename]
    public function defaultFileName($sourcecode) {
            return 'prog.sh';
    }
    
    public function getRunCommand(){
        return array("$(pwd)/prog.sh");
    }

    public function getExecutablePath() {
        return '/bin/bash';
    }



    public function getTargetFile() {
        return 'prog.sh';
    }


    // Get rid of the tab characters at the start of indented lines in
    // traceback output.
    public function filteredStderr() {
        return str_replace("\n\t", "\n        ", $this->stderr);
    }
};


